import json
from pathlib import Path
from typing import List, Dict, Any, Set

import streamlit as st


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _load_results() -> Dict[str, Any] | None:
    path = _project_root() / "results.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _init_session_state() -> None:
    if "saved_jobs" not in st.session_state:
        st.session_state["saved_jobs"] = set()  # type: ignore[assignment]
    if "dismissed_jobs" not in st.session_state:
        st.session_state["dismissed_jobs"] = set()  # type: ignore[assignment]


def _score_to_color_and_label(tag: str) -> str:
    mapping = {
        "intern": "#2ecc71",      # green
        "new grad": "#3498db",    # blue
        "full-time": "#e67e22",   # orange
    }
    key = tag.lower()
    return mapping.get(key, "#bdc3c7")  # grey fallback


def _stars_to_color(stars: str) -> str:
    if stars == "★★★★":
        return "#2ecc71"  # green
    if stars == "★★★":
        return "#3498db"  # blue
    if stars == "★★":
        return "#e67e22"  # orange
    if stars == "★":
        return "#7f8c8d"  # grey
    return "#7f8c8d"


def main() -> None:
    st.set_page_config(page_title="Job Finder", page_icon="🎯", layout="wide")
    _init_session_state()

    data = _load_results()
    if not data:
        st.title("Job Finder Dashboard")
        st.info("No results found. Run `python matcher.py` to generate results.")
        return

    run_at = data.get("run_at", "N/A")
    fetched_total = int(data.get("fetched_total", 0))
    matched_total = int(data.get("matched_total", 0))
    avg_score = float(data.get("avg_score", 0.0))
    jobs: List[Dict[str, Any]] = data.get("jobs", [])

    st.title("Job Finder Dashboard 🎯")
    st.markdown(
        f"**Last run:** {run_at} &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"**Fetched:** {fetched_total} &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"**Matched:** {matched_total} &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"**Avg score:** {avg_score:.2f}"
    )

    # Score distribution (all matched roles)
    if jobs:
        scores_all = [j.get("score", 0.0) for j in jobs]
        st.subheader(f"Score distribution — all {len(jobs)} matched roles")
        st.bar_chart(scores_all)

    # Sidebar filters
    st.sidebar.header("Filters")
    search_term = st.sidebar.text_input("Search (title or company)", "").strip().lower()

    all_tags = sorted({(j.get("tag") or "FULL-TIME").upper() for j in jobs})
    default_tags = all_tags or ["INTERN", "NEW GRAD", "FULL-TIME"]
    selected_tags = st.sidebar.multiselect(
        "Job type", options=["INTERN", "NEW GRAD", "FULL-TIME"], default=default_tags
    )

    all_locations = sorted({j.get("location") or "N/A" for j in jobs})
    selected_locations = st.sidebar.multiselect(
        "Location", options=all_locations, default=all_locations
    )

    min_score = st.sidebar.slider(
        "Minimum score", min_value=0.10, max_value=1.00, value=0.20, step=0.05
    )

    sort_by = st.sidebar.selectbox(
        "Sort by", options=["Score (highest first)", "Date posted (newest first)"]
    )

    saved_only = st.sidebar.checkbox("Saved jobs only", value=False)

    saved_jobs: Set[str] = st.session_state["saved_jobs"]  # type: ignore[assignment]
    dismissed_jobs: Set[str] = st.session_state["dismissed_jobs"]  # type: ignore[assignment]

    # Apply filters
    filtered = []
    for job in jobs:
        title = (job.get("title") or "").lower()
        company = (job.get("company") or "").lower()
        location = job.get("location") or "N/A"
        tag = (job.get("tag") or "FULL-TIME").upper()
        score = float(job.get("score", 0.0))
        url = job.get("url") or ""

        if url in dismissed_jobs:
            continue
        if saved_only and url not in saved_jobs:
            continue
        if search_term and not (search_term in title or search_term in company):
            continue
        if tag not in selected_tags:
            continue
        if location not in selected_locations:
            continue
        if score < min_score:
            continue

        filtered.append(job)

    # Sorting
    if sort_by == "Score (highest first)":
        filtered.sort(key=lambda j: float(j.get("score", 0.0)), reverse=True)
    else:
        # Newest first by posted_at
        filtered.sort(key=lambda j: j.get("posted_at") or "", reverse=True)

    st.subheader(f"Results ({len(filtered)} shown)")

    if not filtered:
        st.warning("No jobs match your current filters. Try adjusting the sidebar.")
        return

    for job in filtered:
        url = job.get("url") or ""
        score = float(job.get("score", 0.0))
        stars = job.get("stars") or ""
        raw_tag = job.get("tag") or "FULL-TIME"
        tag = raw_tag.upper()

        title = job.get("title") or "N/A"
        company = job.get("company") or "N/A"
        location = job.get("location") or "N/A"
        posted_at = job.get("posted_at") or "N/A"
        description = (job.get("description") or "").strip()

        tag_color = _score_to_color_and_label(tag)
        star_color = _stars_to_color(stars)

        with st.container(border=True):
            # Top line
            st.markdown(
                f"<span style='font-weight:bold;'>score={score:.2f}</span> "
                f"<span style='color:{star_color}; font-weight:bold;'>{stars}</span> "
                f"<span style='color:{tag_color}; font-weight:bold;'>[{tag}]</span>",
                unsafe_allow_html=True,
            )

            # Title as link
            if url:
                st.markdown(f"### [{title}]({url})")
            else:
                st.markdown(f"### {title}")

            st.markdown(f"**{company}**  |  {location}  |  Posted: {posted_at}")

            st.markdown(description[:300] + ("..." if len(description) > 300 else ""))

            cols = st.columns(2)
            with cols[0]:
                if url in saved_jobs:
                    if st.button("✅ Saved", key=f"unsave-{url}"):
                        saved_jobs.discard(url)
                        st.session_state["saved_jobs"] = saved_jobs
                        st.rerun()
                else:
                    if st.button("⭐ Save", key=f"save-{url}"):
                        saved_jobs.add(url)
                        st.session_state["saved_jobs"] = saved_jobs
                        st.rerun()
            with cols[1]:
                if st.button("🚫 Dismiss", key=f"dismiss-{url}"):
                    dismissed_jobs.add(url)
                    st.session_state["dismissed_jobs"] = dismissed_jobs
                    st.rerun()


if __name__ == "__main__":
    main()

