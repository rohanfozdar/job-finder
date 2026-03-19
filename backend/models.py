from typing import List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for the /search endpoint."""

    job_title: str = Field(..., description="Target job title or keywords.")
    location: str = Field(..., description="City, region, or 'Remote'.")
    max_results: int = Field(
        20,
        description="Maximum number of jobs to return (default 20, max 50).",
        ge=1,
        le=50,
    )


class JobResult(BaseModel):
    """Normalized job listing returned to the frontend."""

    id: str
    title: str
    company: str
    location: str
    posted_at: str
    url: str
    description: str
    job_type: str
    ai_score: Optional[float] = None


class SearchResponse(BaseModel):
    """Response for the /search endpoint."""

    total_fetched: int
    jobs: List[JobResult]

