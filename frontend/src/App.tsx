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

  const handleSearchComplete = (results: Job[], jobTitle: string, location: string) => {
    setJobs(results);
    setSearchContext({ jobTitle, location });
    setPage("results");
  };

  const handleBackToHome = () => {
    setPage("home");
    setJobs([]);
    setSearchContext(null);
  };

  if (page === "results" && searchContext) {
    return (
      <ResultsPage
        jobs={jobs}
        jobTitle={searchContext.jobTitle}
        location={searchContext.location}
        onBack={handleBackToHome}
      />
    );
  }

  return <HomePage onSearchComplete={handleSearchComplete} />;
};

export default App;

