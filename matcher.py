import os, logging, warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

import argparse
import contextlib
import io
from statistics import mean
from typing import List, Dict, Any, Optional, Tuple

from ingestor import fetch_jobs
from vector_brain import query_profile
from candidate_profile import PROFILE
from notifier import save_log, send_email, save_results_json


SCORE_THRESHOLD = 0.20
MAX_RESULTS     = 20
TOP_K           = 5


def _safe_text(value: Optional[str]) -> str:
    """
    Return a safe string for display and embedding.
    """
    return (value or "").strip()


def build_job_text(job: Dict[str, Any]) -> str:
    """
    Build a single string that combines title + company + location + description.

    This is the text that gets embedded and compared against the resume/profile
    vector store for semantic scoring.
    """
    title = _safe_text(job.get("job_title"))
    comp  = _safe_text(job.get("company_name"))
    loc   = _safe_text(job.get("location"))
    desc  = _safe_text(job.get("description"))

    parts = [
        f"Title: {title}",
        f"Company: {comp}",
        f"Location: {loc}",
        f"Description: {desc}",
    ]
    return "\n".join(parts).strip()


def _has_deal_breaker(job: Dict[str, Any], deal_breakers: List[str]) -> bool:
    """
    Return True if any deal-breaker phrase appears in the title or description
    (case-insensitive).
    """
    haystack = f"{_safe_text(job.get('job_title'))}\n{_safe_text(job.get('description'))}".lower()
    return any(phrase.lower() in haystack for phrase in deal_breakers)


def score_job(job: Dict[str, Any], top_k: int = TOP_K) -> Tuple[float, List[Dict[str, Any]], bool]:
    """
    Score a single job using the vector store.

    Score = mean of the top_k chunk similarity scores returned by query_profile().
    Deal-breaker penalty: if any phrase appears in title/description, multiply
    final score by 0.5.
    """
    job_text = build_job_text(job)
    hits = query_profile(job_text, top_k=top_k)
    base = mean([h["score"] for h in hits]) if hits else 0.0

    penalized = _has_deal_breaker(job, PROFILE.get("deal_breakers", []))
    final = base * 0.5 if penalized else base
    return final, hits, penalized


def stars_for_score(score: float) -> str:
    """
    Convert a numeric match score into a star rating.
    """
    if score >= 0.45:
        return "★★★★"
    if score >= 0.35:
        return "★★★"
    if score >= 0.25:
        return "★★"
    if score >= 0.10:
        return "★"
    return ""


def job_type_tag(title: str) -> str:
    """
    Classify a job as INTERN, NEW GRAD, or FULL-TIME based on the title text.
    """
    t = (title or "").lower()
    if "intern" in t:
        return "[INTERN]"
    if any(x in t for x in ["new grad", "entry", "junior", "associate"]):
        return "[NEW GRAD]"
    return "[FULL-TIME]"


def _print_ranked_results(
    scored: List[Dict[str, Any]],
    fetched_total: int,
    penalties_applied: int,
) -> None:
    """
    Print the ranked list and summary in the required terminal format.
    """
    divider = "═" * 72
    print(f"\n{divider}")
    print(f"  RANKED RESULTS — {len(scored)} roles matched (of {fetched_total} fetched)")
    print(f"{divider}\n")

    if not scored:
        print("No roles met the score threshold.\n")
        print(f"Avg score: 0.00 | Best: N/A | Deal-breaker penalties applied: {penalties_applied}")
        return

    for i, row in enumerate(scored, start=1):
        job   = row["job"]
        score = row["score"]

        title   = job.get("job_title") or "N/A"
        company = job.get("company_name") or "N/A"
        loc     = job.get("location") or "N/A"
        posted  = (_safe_text(job.get("posted_at")) or "N/A")[:10]
        url     = job.get("job_url") or "N/A"
        snippet = (_safe_text(job.get("description")) or "").replace("\n", " ")
        snippet = snippet[:200] + "..." if len(snippet) > 200 else snippet

        stars = stars_for_score(score)
        tag   = job_type_tag(title)

        print(f"[{i:02d}] score={score:.2f}  {stars}  {tag}")
        print(f"     Title    : {title}")
        print(f"     Company  : {company}")
        print(f"     Location : {loc}")
        print(f"     Posted   : {posted}")
        print(f"     URL      : {url}")
        print(f"     Summary  : {snippet}")

        if row.get("debug_hits"):
            print("     Debug    : chunk scores")
            for h in row["debug_hits"]:
                s = h["score"]
                c = _safe_text(h["chunk"]).replace("\n", " ")
                c = c[:120] + "..." if len(c) > 120 else c
                print(f"               - {s:.4f} | {c}")

        print()

    avg_score = mean([r["score"] for r in scored]) if scored else 0.0
    best = scored[0]
    best_job = best["job"]
    best_title = best_job.get("job_title") or "N/A"
    best_company = best_job.get("company_name") or "N/A"

    print(
        f"Avg score: {avg_score:.2f} | "
        f"Best: {best['score']:.2f} ({best_title} @ {best_company}) | "
        f"Deal-breaker penalties applied: {penalties_applied}"
    )


def main() -> None:
    """
    Entrypoint: fetch jobs, score each job against the vector store, apply
    deal-breaker penalties, then print a ranked shortlist.
    """
    parser = argparse.ArgumentParser(description="Quant-Match Phase 3: Matching Agent")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the individual chunk scores for each displayed job.",
    )
    args = parser.parse_args()

    # Fetch jobs, but suppress ingestor.py's per-page prints for cleaner output.
    with contextlib.redirect_stdout(io.StringIO()):
        jobs = fetch_jobs()

    print(f"Fetched {len(jobs)} jobs from Jooble.")

    scored_rows: List[Dict[str, Any]] = []
    penalties_applied = 0

    for job in jobs:
        score, hits, penalized = score_job(job, top_k=TOP_K)
        if penalized:
            penalties_applied += 1

        if score >= SCORE_THRESHOLD:
            scored_rows.append(
                {
                    "job": job,
                    "score": score,
                    "debug_hits": hits if args.debug else None,
                }
            )

    scored_rows.sort(key=lambda r: r["score"], reverse=True)
    scored_rows = scored_rows[:MAX_RESULTS]

    _print_ranked_results(
        scored=scored_rows,
        fetched_total=len(jobs),
        penalties_applied=penalties_applied,
    )

    # Save log file
    save_log(scored_jobs=scored_rows, fetched_total=len(jobs))

    # Send email
    send_email(scored_jobs=scored_rows, fetched_total=len(jobs))

    # Save JSON results for Streamlit dashboard
    save_results_json(scored_jobs=scored_rows, fetched_total=len(jobs))


if __name__ == "__main__":
    main()

