import React, { useState } from "react";
import HomePage from "./pages/HomePage";
import ResultsPage from "./pages/ResultsPage";
import type { Job } from "./types/job";

type Page = "home" | "results";

interface SearchContext {
  jobTitle: string;
  location: string;
}

const App: React.FC = () => {
  const [page, setPage] = useState<Page>("home");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [searchContext, setSearchContext] = useState<SearchContext | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const handleSearchComplete = (
    results: Job[],
    jobTitle: string,
    location: string,
    file: File | null
  ) => {
    setJobs(results);
    setSearchContext({ jobTitle, location });
    setResumeFile(file);
    setPage("results");
  };

  const handleBackToHome = () => {
    setPage("home");
    setJobs([]);
    setSearchContext(null);
    setResumeFile(null);
  };

  if (page === "results" && searchContext) {
    return (
      <ResultsPage
        jobs={jobs}
        setJobs={setJobs}
        resumeFile={resumeFile}
        jobTitle={searchContext.jobTitle}
        location={searchContext.location}
        onBack={handleBackToHome}
      />
    );
  }

  return <HomePage onSearchComplete={handleSearchComplete} />;
};

export default App;

