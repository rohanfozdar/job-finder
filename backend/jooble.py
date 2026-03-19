from __future__ import annotations

import html
import os
import re
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from requests import RequestException


load_dotenv()


def clean_description(text: str) -> str:
    """
    Clean HTML snippets from Jooble into plain text:
    - Unescape entities
    - Strip HTML tags
    - Collapse whitespace
    """
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_api_key() -> str:
    """Read the Jooble API key from the environment."""
    key = os.getenv("JOOBLE_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "JOOBLE_API_KEY is not set. Add it to your environment or backend/.env file."
        )
    return key


def _build_url() -> str:
    """Build the Jooble POST URL."""
    api_key = _get_api_key()
    return f"https://jooble.org/api/{api_key}"


def _normalize_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map Jooble's job fields to our normalized schema."""
    title = raw.get("title") or ""
    company = raw.get("company") or ""
    location = raw.get("location") or ""
    posted_at = raw.get("updated") or raw.get("date") or ""
    url = raw.get("link") or ""
    desc_raw = raw.get("snippet") or ""
    desc = clean_description(desc_raw)

    job_type = "FULL-TIME"
    lowered = title.lower()
    if "intern" in lowered:
        job_type = "INTERN"
    elif any(x in lowered for x in ["new grad", "entry", "junior", "associate"]):
        job_type = "NEW GRAD"

    norm = {
        "id": url or f"{title}-{company}-{posted_at}",
        "title": title,
        "company": company,
        "location": location,
        "posted_at": posted_at,
        "url": url,
        "description": desc[:400] + "..." if len(desc) > 400 else desc,
        "job_type": job_type,
        "ai_score": None,
    }
    return norm


def search_jobs(keywords: str, location: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Call the Jooble API and return a deduplicated list of normalized job dicts.

    - Up to 3 pages
    - 20 results per page
    - Sorted newest first by posted_at/updated
    - On error, returns an empty list without raising.
    """
    url = _build_url()
    headers = {"Content-Type": "application/json"}

    per_page = 20
    max_pages = 3

    all_jobs: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        body = {
            "keywords": keywords,
            "location": location,
            "page": str(page),
            "ResultOnPage": str(per_page),
        }

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=15)
        except RequestException:
            # Network / timeout / other request issues — fail gracefully.
            return []

        if resp.status_code >= 400:
            # Any API error — fail gracefully.
            return []

        try:
            data = resp.json()
        except ValueError:
            return []

        raw_jobs = data.get("jobs") or data.get("items") or []
        if not isinstance(raw_jobs, list) or not raw_jobs:
            break

        for raw in raw_jobs:
            norm = _normalize_job(raw)
            url_key = norm.get("url") or norm["id"]
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            all_jobs.append(norm)

        if len(all_jobs) >= max_results:
            break

    # Sort by posted_at (newest first) if available
    all_jobs.sort(key=lambda j: j.get("posted_at") or "", reverse=True)
    return all_jobs[:max_results]

