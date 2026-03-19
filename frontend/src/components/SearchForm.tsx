import React, { useState, ChangeEvent, FormEvent } from "react";
import LoadingSpinner from "./LoadingSpinner";
import type { Job, SearchResponse } from "../types/job";

interface SearchFormProps {
  onResults: (jobs: Job[], jobTitle: string, location: string) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({ onResults }) => {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [location, setLocation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      setResumeFile(null);
    } else {
      setError(null);
      setResumeFile(file || null);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!jobTitle.trim()) {
      setError("Please enter a job title.");
      return;
    }
    if (!location.trim()) {
      setError("Please enter a location.");
      return;
    }

    setLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || "/api";
      const resp = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_title: jobTitle.trim(),
          location: location.trim(),
          max_results: 20,
        }),
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `Request failed with status ${resp.status}`);
      }

      const data: SearchResponse = await resp.json();
      onResults(data.jobs, jobTitle.trim(), location.trim());
    } catch (err: any) {
      setError(err.message || "Failed to fetch jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-card rounded-lg p-6 shadow-lg border border-slate-700 space-y-4"
    >
      {error && (
        <div className="px-4 py-2 text-sm rounded-md bg-red-500/10 text-red-300 border border-red-500/40">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-semibold mb-1">Upload Resume (PDF)</label>
        <div className="border-2 border-dashed border-slate-600 rounded-md p-4 text-sm text-text/80 bg-background flex flex-col items-center justify-center">
          <input
            id="resume"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="hidden"
          />
          <label
            htmlFor="resume"
            className="cursor-pointer px-3 py-1 rounded-md border border-slate-500 hover:border-primary hover:text-primary"
          >
            {resumeFile ? "Change file" : "Click to upload"}
          </label>
          <p className="mt-2 text-xs text-text/60">
            {resumeFile ? resumeFile.name : "No file selected."}
          </p>
          <p className="mt-1 text-xs text-text/60">
            Your resume is processed locally and never stored.
          </p>
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1">Job title</label>
        <input
          type="text"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          placeholder="e.g. AI Engineer Intern, Quantitative Research Intern"
          className="w-full px-3 py-2 rounded-md bg-background border border-slate-600 text-sm focus:outline-none focus:border-primary"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1">Location</label>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. New York, Remote, Chicago"
          className="w-full px-3 py-2 rounded-md bg-background border border-slate-600 text-sm focus:outline-none focus:border-primary"
        />
      </div>

      <div className="pt-2">
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center px-4 py-2 rounded-md bg-primary text-white font-semibold hover:bg-primary/80 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? <LoadingSpinner /> : "Search Jobs 🔍"}
        </button>
      </div>
    </form>
  );
};

export default SearchForm;

