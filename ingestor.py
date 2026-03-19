import os
import time
from typing import List, Dict, Any, Optional

import requests
from requests.exceptions import Timeout, RequestException
from dotenv import load_dotenv
from us_locations import US_LOCATIONS


# ==============================
# Configuration
# ==============================

load_dotenv()


def _normalize_env_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and (
        (value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")
    ):
        value = value[1:-1].strip()
    return value if value else None


# Jooble direct API — get your free key at https://jooble.org/api/about
# Key format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# .env entry: JOOBLE_API_KEY=your-key-here
JOOBLE_API_KEY = _normalize_env_value(os.getenv("JOOBLE_API_KEY"))

# ── Search config ─────────────────────────────────────────────────────────────
API_SEARCH_KEYWORDS = [
    "AI Engineer Intern",
    "Machine Learning Engineer Intern",
    "Quantitative Research Intern",
    "AI Engineer New Grad",
    "NLP Engineer Intern",
    "Software Engineer AI Intern",
]

TARGET_LOCATIONS = [
    "New York, NY",
    "San Francisco, CA",
    "Chicago, IL",
    "Seattle, WA",
    "Boston, MA",
    "Austin, TX",
    "Los Angeles, CA",
    "Washington, DC",
    "Atlanta, GA",
    "Miami, FL",
    "Denver, CO",
    "Remote",
]

KEYWORD_FILTERS = [
    "ai engineer",
    "ai engineering",
    "artificial intelligence engineer",
    "machine learning engineer",
    "ml engineer",
    "software engineer intern",
    "data science intern",
    "data scientist intern",
    "new grad",
    "entry level",
    "entry-level",
    "quantitative research",
    "quant research",
    "quant developer",
    "nlp engineer",
    "nlp intern",
]

NEGATIVE_TITLE_FILTERS = [
    "java",
    "ios",
    "android",
    "frontend",
    "front-end",
    "backend",
    "back-end",
    "devops",
    "salesforce",
    "sap",
    "ruby",
    "php",
    "react",
    "node",
    ".net",
    "c++",
    "embedded",
    "hardware",
    "network engineer",
    "security engineer",
    "qa engineer",
    "test engineer",
    "technical writer",
]

MAX_PAGES        = 3
RESULTS_PER_PAGE = 20
DEBUG            = True   # prints raw response on first request


# ==============================
# Request helpers
# ==============================

def get_url() -> str:
    """
    Jooble's endpoint: POST https://jooble.org/api/{api_key}
    The key goes IN the URL path — no auth header needed.
    """
    if not JOOBLE_API_KEY:
        raise RuntimeError(
            "JOOBLE_API_KEY is not set.\n"
            "1. Go to https://jooble.org/api/about and fill out the form.\n"
            "2. They will email you a UUID key.\n"
            "3. Add to your .env:  JOOBLE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        )
    return f"https://jooble.org/api/{JOOBLE_API_KEY}"


def build_request_body(keywords: str, location: str, page: int) -> Dict[str, Any]:
    return {
        "keywords":     keywords,
        "location":     location,
        "page":         str(page),
        "ResultOnPage": str(RESULTS_PER_PAGE),
    }


def extract_jobs_from_response(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("jobs", "items", "results"):
        if key in data and isinstance(data[key], list):
            return data[key]
    return []


def normalize_job_record(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_title":    job.get("title"),
        "company_name": job.get("company"),
        "location":     job.get("location"),
        "posted_at":    job.get("updated"),
        "job_url":      job.get("link"),
        "description":  job.get("snippet"),
    }


# ==============================
# Filters
# ==============================

def passes_keyword_filter(job: Dict[str, Any]) -> bool:
    title = (job.get("job_title") or "").lower()
    desc  = (job.get("description") or "").lower()
    if any(neg in title for neg in NEGATIVE_TITLE_FILTERS):
        return False
    if any(kw in title for kw in KEYWORD_FILTERS):
        return True
    strong = ["ai engineer", "machine learning engineer", "ml engineer"]
    return any(kw in desc for kw in strong)


def location_matches_us_filters(location: Optional[str]) -> bool:
    """
    Accept a job location if it is in the US or Remote.

    Logic (in order):
    1. If location is empty → reject
    2. If "remote" is in the string → accept immediately
    3. If any non-US country signal is in the string → reject
    4. Tokenize the location string and check if ANY token (or
       bigram) matches an entry in US_LOCATIONS → accept if found
    5. Otherwise → reject

    Analogy: the function carries a complete US address book.
    Any location that contains a recognized US place name passes,
    anything flagged as non-US fails, and pure gibberish is rejected.
    """
    if not location:
        return False

    loc = location.lower().strip()

    # Rule 1: Remote is always accepted
    if "remote" in loc:
        return True

    # Rule 2: Reject known non-US locations
    non_us = [
        "canada", "ontario", "toronto", "vancouver", "montreal",
        "uk", "united kingdom", "london", "england", "scotland",
        "australia", "sydney", "melbourne", "brisbane",
        "india", "bangalore", "mumbai", "delhi", "hyderabad", "pune",
        "germany", "berlin", "munich", "frankfurt",
        "france", "paris",
        "mexico", "brazil", "philippines", "pakistan",
        "singapore", "hong kong", "china", "japan", "korea",
        "netherlands", "sweden", "ireland", "spain", "italy",
    ]
    if any(n in loc for n in non_us):
        return False

    # Rule 3: Tokenize into single words and bigrams, check against
    # US_LOCATIONS. This catches "New York", "NY", "San Francisco",
    # "CA", "Greater Boston Area" etc.
    tokens = loc.replace(",", " ").replace(".", " ").split()
    unigrams = set(tokens)
    bigrams  = {f"{tokens[i]} {tokens[i+1]}"
                for i in range(len(tokens) - 1)}
    trigrams = {f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}"
                for i in range(len(tokens) - 2)}
    all_ngrams = unigrams | bigrams | trigrams

    return bool(all_ngrams & US_LOCATIONS)


# ==============================
# Fetch
# ==============================

def fetch_jobs(search_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    url     = get_url()
    headers = {"Content-Type": "application/json"}

    if search_keywords is None:
        search_keywords = API_SEARCH_KEYWORDS

    all_jobs:      List[Dict[str, Any]] = []
    seen_urls:     set                  = set()
    first_request: bool                 = True

    for search_keyword in search_keywords:
        for location in TARGET_LOCATIONS:
            print(f"\n── Searching: '{search_keyword}' in {location} ──")

            for page in range(1, MAX_PAGES + 1):
                body = build_request_body(search_keyword, location, page)

                try:
                    response = requests.post(url, headers=headers, json=body, timeout=15)
                except Timeout:
                    print(f"  [WARN] Timed out on page {page}. Skipping to next location.")
                    break
                except RequestException as e:
                    print(f"  [ERROR] Request failed: {e}")
                    break

                if DEBUG and first_request:
                    print(f"\n  [DEBUG] Status  : {response.status_code}")
                    print(f"  [DEBUG] Response : {response.text[:600]}\n")
                    first_request = False

                if response.status_code == 403:
                    raise RuntimeError(
                        "403 Forbidden — your Jooble API key is invalid or not yet activated.\n"
                        "Check your email for the key from jooble.org/api/about."
                    )
                elif response.status_code == 404:
                    raise RuntimeError(
                        "404 Not Found — the key in the URL is wrong or the key hasn't been approved yet.\n"
                        f"URL used: {url}"
                    )
                elif response.status_code >= 400:
                    print(f"  [ERROR] Status {response.status_code}: {response.text[:200]}")
                    break

                try:
                    data = response.json()
                except ValueError:
                    print(f"  [ERROR] Could not parse JSON. Raw: {response.text[:300]}")
                    break

                raw_jobs = extract_jobs_from_response(data)
                if not raw_jobs:
                    print(f"  [INFO] No results on page {page}. Stopping pagination.")
                    break

                print(f"  Page {page}: {len(raw_jobs)} raw", end="")

                page_matches = 0
                for job in raw_jobs:
                    normalized = normalize_job_record(job)
                    job_url    = normalized.get("job_url") or ""
                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)
                    if location_matches_us_filters(normalized["location"]) \
                            and passes_keyword_filter(normalized):
                        all_jobs.append(normalized)
                        page_matches += 1

                print(f"  →  {page_matches} matched")
                time.sleep(0.5)

    all_jobs.sort(key=lambda j: j.get("posted_at") or "", reverse=True)
    return all_jobs


# ==============================
# Terminal display
# ==============================

def print_results(jobs: List[Dict[str, Any]]) -> None:
    divider = "=" * 72
    print(f"\n{divider}")
    print(f"  RESULTS: {len(jobs)} matching roles found")
    print(divider)

    if not jobs:
        print("\n  No matching jobs found.")
        print("  If [DEBUG] showed jobs above but none passed filters,")
        print("  loosen KEYWORD_FILTERS or location_matches_us_filters().\n")
        return

    for i, job in enumerate(jobs, start=1):
        title   = job.get("job_title")    or "N/A"
        company = job.get("company_name") or "N/A"
        loc     = job.get("location")     or "N/A"
        posted  = (job.get("posted_at")   or "N/A")[:10]
        url     = job.get("job_url")      or "N/A"
        snippet = (job.get("description") or "").strip()
        snippet = snippet[:200] + "..." if len(snippet) > 200 else snippet

        print(f"\n[{i:02d}]  {title}")
        print(f"      Company  : {company}")
        print(f"      Location : {loc}")
        print(f"      Posted   : {posted}")
        print(f"      URL      : {url}")
        if snippet:
            print(f"      Summary  : {snippet}")

    print(f"\n{divider}\n")


# ==============================
# Entrypoint
# ==============================

def main() -> None:
    key_preview = (JOOBLE_API_KEY or "")[:8]
    print(f"API  : Jooble direct (jooble.org)")
    print(f"Key  : {key_preview}***")
    print(f"Debug: ON\n")

    jobs = fetch_jobs()
    print_results(jobs)


if __name__ == "__main__":
    main()