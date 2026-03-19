"""
Run this ONCE to find the correct Jooble RapidAPI endpoint path.
It tries every plausible path and prints the status + response for each.

Usage:
    python probe_endpoint.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

KEY  = os.getenv("JOOBLE_API_KEY", "").strip().strip('"').strip("'")
HOST = os.getenv("JOOBLE_API_HOST", "jooble.p.rapidapi.com").strip().strip('"').strip("'")

headers = {
    "x-rapidapi-key":  KEY,
    "x-rapidapi-host": HOST,
    "Content-Type":    "application/json",
}

body = {"keywords": "software engineer", "location": "New York", "page": "1"}

candidates = [
    "/",
    "/api",
    "/api/",
    "/jobs",
    "/jobs/search",
    "/search",
    "/v1/jobs",
    "/v1/search",
]

print(f"Key   : {KEY[:8]}***")
print(f"Host  : {HOST}\n")
print(f"{'Status':<8} {'Path':<20} Response (first 150 chars)")
print("-" * 72)

for path in candidates:
    url = f"https://{HOST}{path}"
    try:
        r = requests.post(url, headers=headers, json=body, timeout=10)
        preview = r.text[:150].replace("\n", " ")
        print(f"{r.status_code:<8} {path:<20} {preview}")
    except Exception as e:
        print(f"{'ERR':<8} {path:<20} {e}")