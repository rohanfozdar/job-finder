import React from "react";
import SearchForm from "../components/SearchForm";
import type { Job } from "../types/job";

interface HomePageProps {
  onSearchComplete: (jobs: Job[], jobTitle: string, location: string, resumeFile: File | null) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onSearchComplete }) => {
  return (
    <div className="min-h-screen bg-background text-text flex flex-col">
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-10">
        <section className="max-w-3xl w-full text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4 flex items-center justify-center gap-2">
            <span>AutoSearch</span> <span>🔍</span>
          </h1>
          <p className="text-text/80 text-sm md:text-base">
            Upload your resume, tell us what you're looking for, and we'll find the best matches
            instantly.
          </p>
        </section>

        <section className="max-w-3xl w-full">
          <SearchForm onResults={onSearchComplete} />
        </section>
      </main>

      <footer className="py-4 text-center text-xs text-text/60 border-t border-slate-800">
        Built with FastAPI + React
      </footer>
    </div>
  );
};

export default HomePage;

