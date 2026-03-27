"""
In-memory AI scoring for job listings against a resume.
No disk I/O — resume and jobs are passed in; no vector_store or files used.
"""

from typing import Dict, List, Any

import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


PROFILE: Dict[str, Any] = {
    "name": "Rohan Fozdar",
    "university": "Knox College",
    "gpa": "3.89",
    "graduation_year": "2026",
    "target_titles": [
        "AI Engineer Intern",
        "Machine Learning Engineer Intern",
        "Software Engineer Intern (AI/ML)",
        "AI Engineering Intern",
        "Quantitative Research Intern",
        "Quant Developer Intern",
        "NLP Engineer Intern",
        "AI Agent Engineer Intern",
        "AI Engineer New Grad",
        "Machine Learning Engineer New Grad",
        "Junior AI Engineer",
        "Junior Machine Learning Engineer",
        "Junior Quantitative Researcher",
        "New Grad Software Engineer (AI/ML)",
    ],
    "skills": [
        "Python",
        "PyTorch",
        "TensorFlow",
        "LangChain",
        "HuggingFace",
        "SQL",
        "NumPy",
        "Pandas",
        "Java",
        "MATLAB",
        "SAS",
        "Tableau",
        "Power BI",
        "Excel",
        "Matplotlib",
        "neural networks",
        "convolutional neural networks",
        "CNNs",
        "recurrent neural networks",
        "RNNs",
        "large language models",
        "LLMs",
        "deep learning",
        "fine-tuning",
        "transformers",
        "natural language processing",
        "NLP",
        "AI agents",
        "agentic workflows",
        "LangChain agents",
        "retrieval augmented generation",
        "RAG",
        "quantitative modeling",
        "options pricing",
        "derivatives",
        "binomial tree",
        "implied volatility",
        "momentum trading",
        "backtesting",
        "time series analysis",
        "algorithmic trading",
        "Sharpe ratio",
        "CAGR",
        "risk management",
        "machine learning",
        "data science",
        "mathematics",
        "statistics",
        "preprocessing pipelines",
        "GPT fine-tuning",
    ],
    "projects": [
        "Options Pricing Engine: Binomial tree pricer for American options with 3D Implied Volatility "
        "surface visualization",
        "Moving Average Exposure Model: Validated trends using CMP against 5/10/20/50/200 MAs for Indian "
        "NSE markets, achieving 3100% returns and 5.86 Sharpe over 25 years of backtested daily data",
        "Momentum Trading Strategy: Time trend derivatives on NSE ETFs, backtested on 1 year of "
        "tick-by-tick BankNifty data achieving 45% returns and 8.43 Sharpe",
        "ParserAuto: Preprocessing pipeline normalizing heterogeneous transcript formats, validated against "
        "production requirements via fine-tuning early GPT models",
    ],
    "interests": [
        "building AI agents and agentic workflows",
        "quantitative finance and algorithmic trading",
        "natural language processing",
        "large language model fine-tuning and deployment",
        "retrieval augmented generation systems",
        "financial machine learning",
        "AI infrastructure for trading and markets",
    ],
    "target_industries": [
        "AI startups",
        "quantitative trading firms",
        "hedge funds",
        "fintech",
        "big tech",
        "financial technology",
    ],
    "job_types": [
        "Summer 2026 internship",
        "new grad full-time",
        "entry level",
    ],
    "preferred_locations": [
        "Chicago",
        "San Francisco",
        "New York",
        "Remote",
    ],
    "deal_breakers": [
        "senior",
        "staff",
        "principal",
        "director",
        "vice president",
        "10+ years",
        "8+ years",
        "7+ years",
        "5+ years",
        "lead engineer",
    ],
}


def build_profile_text() -> str:
    """
    Build a rich paragraph describing who Rohan is, what he has built,
    what skills he has, and which roles and industries he is targeting.

    The text is optimized for semantic embeddings so that the vector
    store can clearly distinguish quant trading internships from,
    for example, insurance analytics roles.
    """
    name = PROFILE["name"]
    university = PROFILE["university"]
    gpa = PROFILE["gpa"]
    grad_year = PROFILE["graduation_year"]
    titles: List[str] = PROFILE["target_titles"]
    skills: List[str] = PROFILE["skills"]
    projects: List[str] = PROFILE["projects"]
    interests: List[str] = PROFILE["interests"]
    industries: List[str] = PROFILE["target_industries"]
    job_types: List[str] = PROFILE["job_types"]
    locations: List[str] = PROFILE["preferred_locations"]
    deal_breakers: List[str] = PROFILE["deal_breakers"]

    titles_text = ", ".join(titles[:-1]) + f", and {titles[-1]}"
    skills_text = ", ".join(skills)
    projects_text = " ".join(projects)
    interests_text = ", ".join(interests)
    industries_text = ", ".join(industries)
    job_types_text = ", ".join(job_types)
    locations_text = ", ".join(locations)
    deal_breakers_text = ", ".join(deal_breakers)

    paragraph = (
        f"My name is {name}, a {grad_year} graduate from {university} with a GPA of {gpa}, "
        f"focused on applied machine learning, quantitative modeling, and AI engineering. "
        f"I am actively targeting roles such as {titles_text}, primarily for {job_types_text}, "
        f"in industries including {industries_text}. "
        f"My core technical skills span {skills_text}, and I have used these to build projects like "
        f"{projects_text}. "
        f"I am especially interested in {interests_text}, and I am looking for opportunities in "
        f"{locations_text}. "
        f"I want to avoid roles that are clearly misaligned with early-career AI and quant work, such as "
        f"positions that emphasize {deal_breakers_text}."
    )

    return paragraph


_MODEL = None


def _get_model() -> SentenceTransformer:
    """Load SentenceTransformer once per process."""
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _chunk_text(text: str, chunk_size_words: int = 300, overlap_words: int = 50) -> list[str]:
    """Split text into overlapping chunks (same logic as vector_brain.py)."""
    if not text:
        return []
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start = max(0, end - overlap_words)
    return chunks


def _extract_resume_text(resume_bytes: bytes) -> str:
    """Extract text from resume PDF bytes in memory."""
    doc = fitz.open(stream=resume_bytes, filetype="pdf")
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
    finally:
        doc.close()
    return "\n".join(parts).strip()


def _has_deal_breaker(job: dict, deal_breakers: list) -> bool:
    """True if any deal-breaker phrase appears in title or description (case-insensitive)."""
    title = (job.get("title") or job.get("job_title") or "").lower()
    desc = (job.get("description") or "").lower()
    haystack = f"{title}\n{desc}"
    return any(phrase.lower() in haystack for phrase in deal_breakers)


def score_jobs(resume_bytes: bytes, jobs: list[dict]) -> list[dict]:
    """
    Score and rank a list of jobs against a resume.

    Args:
        resume_bytes: Raw bytes of the resume PDF file
        jobs: List of job dicts, each containing at minimum:
              title, company, location, description, url,
              posted_at, job_type, id

    Returns:
        The same list of job dicts, sorted by ai_score descending,
        with ai_score field populated as a float between 0 and 1.
        Jobs with a deal-breaker match have their score halved.
    """
    # 1. Extract resume text from bytes
    resume_text = _extract_resume_text(resume_bytes)
    resume_chunks = _chunk_text(resume_text, chunk_size_words=300, overlap_words=50)

    # 2. Build profile text and combine chunks
    profile_text = build_profile_text()
    all_chunks = resume_chunks + [profile_text]

    if not all_chunks:
        for job in jobs:
            job["ai_score"] = 0.0
        return jobs

    # 3. Embed all chunks
    model = _get_model()
    embeddings = model.encode(all_chunks, convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(embeddings)

    # 4. Build FAISS index in memory
    num_vectors, dim = embeddings.shape
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # 5. Score each job
    deal_breakers = PROFILE.get("deal_breakers", [])
    top_k = 5

    for job in jobs:
        title = job.get("title") or job.get("job_title") or ""
        company = job.get("company") or job.get("company_name") or ""
        location = job.get("location") or ""
        description = job.get("description") or ""
        job_text = f"{title} {company} {location} {description}".strip()

        if not job_text:
            job["ai_score"] = 0.0
            continue

        query_vec = model.encode([job_text], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(query_vec)

        scores, _ = index.search(query_vec, min(top_k, num_vectors))
        scores = scores[0]
        ai_score = float(np.mean(scores)) if len(scores) > 0 else 0.0

        if _has_deal_breaker(job, deal_breakers):
            ai_score *= 0.5

        job["ai_score"] = round(ai_score, 4)

    # 6. Sort by ai_score descending and return
    jobs.sort(key=lambda j: j.get("ai_score", 0.0), reverse=True)
    return jobs
