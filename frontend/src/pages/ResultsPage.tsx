import React, { useMemo, useState } from "react";
import type { Job } from "../types/job";
import FilterBar from "../components/FilterBar";
import JobCard from "../components/JobCard";

interface ResultsPageProps {
  jobs: Job[];
  setJobs: React.Dispatch<React.SetStateAction<Job[]>>;
  resumeFile: File | null;
  jobTitle: string;
  location: string;
  onBack: () => void;
}

const ResultsPage: React.FC<ResultsPageProps> = ({
  jobs,
  setJobs,
  resumeFile,
  jobTitle,
  location,
  onBack,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedJobTypes, setSelectedJobTypes] = useState<string[]>([
    "INTERN",
    "NEW GRAD",
    "FULL-TIME",
  ]);
  const allLocations = useMemo(
    () => Array.from(new Set(jobs.map((j) => j.location))).sort(),
    [jobs]
  );
  const [selectedLocations, setSelectedLocations] = useState<string[]>(allLocations);
  const [dateFilter, setDateFilter] = useState<string>("any");
  const [sortBy, setSortBy] = useState<string>("date");
  const [savedOnly, setSavedOnly] = useState<boolean>(false);
  const [showSavedTab, setShowSavedTab] = useState<"all" | "saved">("all");
  const [scoringLoading, setScoringLoading] = useState(false);
  const [scoringError, setScoringError] = useState<string | null>(null);

  const handleClearFilters = () => {
    setSearchTerm("");
    setSelectedJobTypes(["INTERN", "NEW GRAD", "FULL-TIME"]);
    setSelectedLocations(allLocations);
    setDateFilter("any");
    setSortBy("date");
    setSavedOnly(false);
    setShowSavedTab("all");
  };

  const savedIds = useMemo(() => {
    const raw = localStorage.getItem("jobfinder_saved_jobs");
    if (!raw) return new Set<string>();
    try {
      const arr: string[] = JSON.parse(raw);
      return new Set(arr);
    } catch {
      return new Set<string>();
    }
  }, [jobs, showSavedTab, savedOnly, searchTerm, selectedJobTypes, selectedLocations, dateFilter, sortBy]);

  const filteredJobs = useMemo(() => {
    const now = new Date();

    return jobs
      .filter((job) => {
        if (showSavedTab === "saved" || savedOnly) {
          if (!savedIds.has(job.id)) return false;
        }

        const lowerTitle = job.title.toLowerCase();
        const lowerCompany = job.company.toLowerCase();
        if (searchTerm) {
          const t = searchTerm.toLowerCase();
          if (!lowerTitle.includes(t) && !lowerCompany.includes(t)) {
            return false;
          }
        }

        if (!selectedJobTypes.includes(job.job_type)) return false;
        if (!selectedLocations.includes(job.location)) return false;

        if (dateFilter !== "any" && job.posted_at) {
          const jobDate = new Date(job.posted_at);
          const diffDays = (now.getTime() - jobDate.getTime()) / (1000 * 60 * 60 * 24);
          const limit = dateFilter === "7" ? 7 : 30;
          if (diffDays > limit) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === "alpha") {
          return a.title.localeCompare(b.title);
        }
        if (sortBy === "score") {
          return (b.ai_score ?? 0) - (a.ai_score ?? 0);
        }
        return (b.posted_at || "").localeCompare(a.posted_at || "");
      });
  }, [
    jobs,
    searchTerm,
    selectedJobTypes,
    selectedLocations,
    dateFilter,
    sortBy,
    savedOnly,
    showSavedTab,
    savedIds,
  ]);

  const allAiNull = jobs.every((j) => j.ai_score == null);

  const handleRunAIScoring = async () => {
    if (!resumeFile) {
      setScoringError("Upload a resume on the home page before running AI scoring.");
      return;
    }
    setScoringError(null);
    setScoringLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || "/api";
      const formData = new FormData();
      formData.append("resume", resumeFile);
      formData.append("jobs", JSON.stringify(jobs));

      const resp = await fetch(`${baseUrl}/score`, {
        method: "POST",
        body: formData,
      });

      const data = await resp.json().catch(() => null);
      if (!resp.ok || (data && "error" in data && data.error)) {
        setScoringError("Scoring failed. Please try again.");
        return;
      }
      if (data && Array.isArray(data.jobs)) {
        setJobs(data.jobs as Job[]);
      } else {
        setScoringError("Scoring failed. Please try again.");
      }
    } catch {
      setScoringError("Scoring failed. Please try again.");
    } finally {
      setScoringLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-text flex flex-col">
      <header className="px-4 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="px-3 py-1 text-sm rounded-md border border-slate-600 hover:border-primary hover:text-primary"
          >
            ← Back
          </button>
          <div>
            <div className="text-sm text-text/80">
              Showing {filteredJobs.length} results for{" "}
              <span className="font-semibold">"{jobTitle}"</span> in{" "}
              <span className="font-semibold">"{location}"</span>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          {scoringError && (
            <span className="text-xs text-red-400 max-w-xs text-right">{scoringError}</span>
          )}
          <button
            type="button"
            onClick={handleRunAIScoring}
            disabled={scoringLoading}
            className="px-4 py-2 text-sm rounded-md bg-primary text-white font-semibold hover:bg-primary/80 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {scoringLoading ? "Scoring... ✨" : "Run AI Scoring ✨"}
          </button>
        </div>
      </header>

      <main className="flex-1 flex flex-col md:flex-row gap-4 px-4 py-4">
        <FilterBar
          searchTerm={searchTerm}
          onSearchTermChange={setSearchTerm}
          jobTypes={["INTERN", "NEW GRAD", "FULL-TIME"]}
          selectedJobTypes={selectedJobTypes}
          onJobTypesChange={setSelectedJobTypes}
          locations={allLocations}
          selectedLocations={selectedLocations}
          onLocationsChange={setSelectedLocations}
          dateFilter={dateFilter}
          onDateFilterChange={setDateFilter}
          sortBy={sortBy}
          onSortByChange={setSortBy}
          onClearFilters={handleClearFilters}
          savedOnly={savedOnly}
          onSavedOnlyChange={setSavedOnly}
        />

        <section className="flex-1 flex flex-col gap-4">
          {allAiNull && (
            <div className="px-4 py-2 text-xs rounded-md bg-card border border-slate-700 text-text/80">
              💡 Results sorted by date. Run AI Scoring to rank by relevance to your resume.
            </div>
          )}

          <div className="flex items-center gap-4 mb-2">
            <button
              type="button"
              onClick={() => setShowSavedTab("all")}
              className={`px-3 py-1 text-xs rounded-md border ${
                showSavedTab === "all"
                  ? "bg-primary text-white border-primary"
                  : "border-slate-600 text-text/80"
              }`}
            >
              All jobs
            </button>
            <button
              type="button"
              onClick={() => setShowSavedTab("saved")}
              className={`px-3 py-1 text-xs rounded-md border ${
                showSavedTab === "saved"
                  ? "bg-primary text-white border-primary"
                  : "border-slate-600 text-text/80"
              }`}
            >
              Saved jobs
            </button>
          </div>

          {filteredJobs.length === 0 ? (
            <div className="mt-4 text-sm text-text/70">
              No jobs match your filters. Try adjusting the sidebar.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredJobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default ResultsPage;

