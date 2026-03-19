"""
Defines a simple candidate profile dictionary and a helper function to
convert that profile into a single paragraph of text for embeddings.
"""

from typing import Dict, List, Any


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

