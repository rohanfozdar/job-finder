import React, { useEffect, useState } from "react";
import type { Job } from "../types/job";

const STORAGE_KEY = "jobfinder_saved_jobs";

interface JobCardProps {
  job: Job;
}

const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const [savedJobs, setSavedJobs] = useState<Set<string>>(new Set());

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const arr: string[] = JSON.parse(raw);
        setSavedJobs(new Set(arr));
      } catch {
        setSavedJobs(new Set());
      }
    }
  }, []);

  const isSaved = savedJobs.has(job.id);

  const persist = (next: Set<string>) => {
    setSavedJobs(new Set(next));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(next)));
  };

  const toggleSave = () => {
    const next = new Set(savedJobs);
    if (next.has(job.id)) {
      next.delete(job.id);
    } else {
      next.add(job.id);
    }
    persist(next);
  };

  const openJob = () => {
    if (job.url) {
      window.open(job.url, "_blank", "noopener,noreferrer");
    }
  };

  const badgeColor =
    job.job_type === "INTERN"
      ? "bg-success/10 text-success border-success/40"
      : job.job_type === "NEW GRAD"
      ? "bg-info/10 text-info border-info/40"
      : "bg-warning/10 text-warning border-warning/40";

  return (
    <div className="bg-card rounded-lg p-4 shadow-md flex flex-col justify-between border border-slate-700">
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${badgeColor}`}>
            {job.job_type}
          </span>
        </div>

        <h3 className="text-lg font-semibold mb-1">
          {job.url ? (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary underline"
            >
              {job.title}
            </a>
          ) : (
            job.title
          )}
        </h3>

        <div className="text-sm text-text/80 mb-1 flex flex-wrap items-center gap-2">
          <span>🏢 {job.company}</span>
          <span>·</span>
          <span>📍 {job.location}</span>
        </div>

        <div className="text-xs text-text/60 mb-2">🗓 {job.posted_at}</div>

        <p className="text-sm text-text/80">
          {job.description.length > 200 ? `${job.description.slice(0, 200)}...` : job.description}
        </p>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <button
          type="button"
          onClick={toggleSave}
          className={`px-3 py-1 text-xs font-semibold rounded-md border transition ${
            isSaved
              ? "bg-success/20 text-success border-success/60"
              : "bg-transparent text-text border-slate-500 hover:border-primary hover:text-primary"
          }`}
        >
          {isSaved ? "✅ Saved" : "⭐ Save"}
        </button>
        <button
          type="button"
          onClick={openJob}
          className="px-3 py-1 text-xs font-semibold rounded-md bg-primary text-white hover:bg-primary/80"
        >
          Apply →
        </button>
      </div>
    </div>
  );
};

export default JobCard;

