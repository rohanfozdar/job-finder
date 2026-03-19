from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

import json

from dotenv import load_dotenv


# NOTE: Outlook/Hotmail may require an App Password (not your normal password)
# when two-factor authentication (2FA) is enabled.
# See: https://support.microsoft.com/en-us/account-billing/app-passwords


def _project_root() -> Path:
    """
    Return the project root directory (assumes this file lives in root).
    """
    return Path(__file__).resolve().parent


def _safe_text(value: Optional[str]) -> str:
    """
    Return a safe, stripped string (never None).
    """
    return (value or "").strip()


def _stars_for_score(score: float) -> str:
    """
    Convert a numeric match score into stars using matcher.py thresholds.
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


def _job_type_tag(title: str) -> str:
    """
    Classify a job as INTERN, NEW GRAD, or FULL-TIME based on the title text.
    """
    t = (title or "").lower()
    if "intern" in t:
        return "[INTERN]"
    if any(x in t for x in ["new grad", "entry", "junior", "associate"]):
        return "[NEW GRAD]"
    return "[FULL-TIME]"


def _normalize_scored_jobs(scored_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure each scored job dict has: job, score, stars, tag.

    matcher.py currently builds dicts with: job, score (and optional debug_hits).
    This function fills stars/tag when missing so notifier can be used without
    changing matcher logic.
    """
    normalized: List[Dict[str, Any]] = []
    for row in scored_jobs:
        job = row.get("job") or {}
        score = float(row.get("score") or 0.0)
        title = _safe_text(job.get("job_title"))

        stars = row.get("stars") or _stars_for_score(score)
        tag = row.get("tag") or _job_type_tag(title)

        normalized.append(
            {
                "job": job,
                "score": score,
                "stars": stars,
                "tag": tag,
            }
        )
    return normalized


def _build_plaintext_report(scored_jobs: List[Dict[str, Any]], fetched_total: int, run_dt: datetime) -> str:
    """
    Build the plain-text report used for both logs and email.
    """
    scored = _normalize_scored_jobs(scored_jobs)

    divider = "═" * 50
    run_str = run_dt.strftime("%Y-%m-%d %H:%M:%S")

    avg = mean([r["score"] for r in scored]) if scored else 0.0

    lines: List[str] = []
    lines.append(divider)
    lines.append(f"JOB FINDER — Run: {run_str}")
    lines.append(f"Fetched: {fetched_total} jobs  |  Matched: {len(scored)}  |  Avg score: {avg:.2f}")
    lines.append(divider)
    lines.append("")

    for i, row in enumerate(scored, start=1):
        job = row["job"]
        score = row["score"]
        stars = row["stars"]
        tag = row["tag"]

        title = job.get("job_title") or "N/A"
        company = job.get("company_name") or "N/A"
        location = job.get("location") or "N/A"
        posted = (_safe_text(job.get("posted_at")) or "N/A")[:10]
        url = job.get("job_url") or "N/A"

        summary = _safe_text(job.get("description")).replace("\n", " ")
        summary = summary[:300] + "..." if len(summary) > 300 else summary

        lines.append(f"[{i:02d}] score={score:.2f}  {stars}  {tag}")
        lines.append(f"     Title    : {title}")
        lines.append(f"     Company  : {company}")
        lines.append(f"     Location : {location}")
        lines.append(f"     Posted   : {posted}")
        lines.append(f"     URL      : {url}")
        lines.append(f"     Summary  : {summary}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def save_log(scored_jobs: List[Dict[str, Any]], fetched_total: int) -> Path:
    """
    Save a timestamped plain-text log file for this run and return its path.
    """
    run_dt = datetime.now()
    logs_dir = _project_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"results_{run_dt.strftime('%Y%m%d_%H%M%S')}.txt"
    path = logs_dir / filename

    report = _build_plaintext_report(scored_jobs=scored_jobs, fetched_total=fetched_total, run_dt=run_dt)
    path.write_text(report, encoding="utf-8")

    print(f"Log saved: {path.as_posix()}")
    return path


def send_email(scored_jobs: List[Dict[str, Any]], fetched_total: int) -> bool:
    """
    Email the ranked results via Outlook/Hotmail SMTP (STARTTLS).

    Returns True on success, False on failure. Never raises exceptions that
    would crash the pipeline.
    """
    load_dotenv()

    sender = _safe_text(os.getenv("EMAIL_SENDER"))
    recipient = _safe_text(os.getenv("EMAIL_RECIPIENT"))
    password = _safe_text(os.getenv("EMAIL_PASSWORD"))

    if not sender or not password:
        print(
            "[INFO] Email not configured — set EMAIL_SENDER and EMAIL_PASSWORD "
            "in .env to enable email delivery."
        )
        return False

    if not recipient:
        recipient = sender

    run_dt = datetime.now()
    date_str = run_dt.strftime("%Y-%m-%d")
    subject = f"Job Finder — {len(scored_jobs)} matches found ({date_str})"

    body = _build_plaintext_report(scored_jobs=scored_jobs, fetched_total=fetched_total, run_dt=run_dt)

    top_title = "N/A"
    top_company = "N/A"
    top_score = 0.0
    if scored_jobs:
        top = _normalize_scored_jobs(scored_jobs)[0]
        job = top["job"]
        top_title = job.get("job_title") or "N/A"
        top_company = job.get("company_name") or "N/A"
        top_score = float(top["score"] or 0.0)

    body += "\n---\n"
    body += f"Sent by Job Finder | Run at {run_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
    body += f"Top match: {top_title} @ {top_company} (score={top_score:.2f})\n"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    host = "smtp-mail.outlook.com"
    port = 587

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender, password)
            server.send_message(msg)
        print("[INFO] Email sent successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")
        return False


def save_results_json(scored_jobs: List[Dict[str, Any]], fetched_total: int) -> None:
    """
    Save a machine-readable results.json file in the project root for
    use by the Streamlit dashboard.
    """
    run_dt = datetime.now()
    scored = _normalize_scored_jobs(scored_jobs)

    matched_total = len(scored)
    avg_score = mean([r["score"] for r in scored]) if scored else 0.0

    jobs_payload: List[Dict[str, Any]] = []
    for i, row in enumerate(scored, start=1):
        job = row["job"]
        score = row["score"]
        stars = row["stars"]
        tag = row["tag"].strip("[]")  # e.g., "[INTERN]" -> "INTERN"

        title = job.get("job_title") or "N/A"
        company = job.get("company_name") or "N/A"
        location = job.get("location") or "N/A"
        posted_at = job.get("posted_at") or "N/A"
        url = job.get("job_url") or "N/A"
        description_full = _safe_text(job.get("description"))
        description = description_full[:400] + "..." if len(description_full) > 400 else description_full

        penalized = bool(row.get("penalized", False))

        jobs_payload.append(
            {
                "rank": i,
                "score": round(float(score), 4),
                "stars": stars,
                "tag": tag,
                "title": title,
                "company": company,
                "location": location,
                "posted_at": posted_at,
                "url": url,
                "description": description,
                "penalized": penalized,
            }
        )

    payload = {
        "run_at": run_dt.isoformat(timespec="seconds"),
        "fetched_total": int(fetched_total),
        "matched_total": int(matched_total),
        "avg_score": round(float(avg_score), 4),
        "jobs": jobs_payload,
    }

    path = _project_root() / "results.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Results JSON saved: {path.as_posix()}")


if __name__ == "__main__":
    dummy_scored = [
        {
            "job": {
                "job_title": "AI Engineer Intern",
                "company_name": "ExampleCo",
                "location": "San Francisco, CA",
                "posted_at": "2026-03-17",
                "job_url": "https://example.com/job1",
                "description": "Work on Python, deep learning, and retrieval systems in an AI agent team.",
            },
            "score": 0.52,
            "stars": "★★★★",
            "tag": "[INTERN]",
        },
        {
            "job": {
                "job_title": "Junior Machine Learning Engineer",
                "company_name": "AnotherCo",
                "location": "New York, NY",
                "posted_at": "2026-03-16",
                "job_url": "https://example.com/job2",
                "description": "Build ML pipelines and evaluate transformer models for NLP applications.",
            },
            "score": 0.33,
            "stars": "★★",
            "tag": "[FULL-TIME]",
        },
    ]

    save_log(scored_jobs=dummy_scored, fetched_total=2)
    send_email(scored_jobs=dummy_scored, fetched_total=2)
    save_results_json(scored_jobs=dummy_scored, fetched_total=2)

