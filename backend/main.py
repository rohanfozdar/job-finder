from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from jooble import search_jobs
from models import SearchRequest, JobResult, SearchResponse


HF_SCORING_URL = "https://rohanfozdar-job-finder-scoring.hf.space/score"


app = FastAPI(title="Job Finder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint for Render."""
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
async def search(body: SearchRequest) -> SearchResponse:
    """
    Search for jobs via the Jooble API.

    Note: The resume file is accepted but not used for scoring yet.
    """
    jobs_raw = search_jobs(
        keywords=body.job_title,
        location=body.location,
        max_results=body.max_results,
    )
    job_results = [JobResult(**j) for j in jobs_raw]
    return SearchResponse(total_fetched=len(job_results), jobs=job_results)


@app.post("/score")
async def score(
    resume: UploadFile = File(...),
    jobs: str = Form(...),
):
    import httpx

    resume_bytes = await resume.read()
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            HF_SCORING_URL,
            files={"resume": ("resume.pdf", resume_bytes, "application/pdf")},
            data={"jobs": jobs},
        )
    return response.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

