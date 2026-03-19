export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  posted_at: string;
  url: string;
  description: string;
  job_type: "INTERN" | "NEW GRAD" | "FULL-TIME";
  ai_score: number | null;
}

export interface SearchResponse {
  total_fetched: number;
  jobs: Job[];
}

