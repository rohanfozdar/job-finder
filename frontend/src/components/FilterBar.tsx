import React from "react";

interface FilterBarProps {
  searchTerm: string;
  onSearchTermChange: (v: string) => void;
  jobTypes: string[];
  selectedJobTypes: string[];
  onJobTypesChange: (types: string[]) => void;
  locations: string[];
  selectedLocations: string[];
  onLocationsChange: (locs: string[]) => void;
  dateFilter: string;
  onDateFilterChange: (v: string) => void;
  sortBy: string;
  onSortByChange: (v: string) => void;
  onClearFilters: () => void;
  savedOnly: boolean;
  onSavedOnlyChange: (v: boolean) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({
  searchTerm,
  onSearchTermChange,
  jobTypes,
  selectedJobTypes,
  onJobTypesChange,
  locations,
  selectedLocations,
  onLocationsChange,
  dateFilter,
  onDateFilterChange,
  sortBy,
  onSortByChange,
  onClearFilters,
  savedOnly,
  onSavedOnlyChange,
}) => {
  const toggleJobType = (type: string) => {
    if (selectedJobTypes.includes(type)) {
      onJobTypesChange(selectedJobTypes.filter((t) => t !== type));
    } else {
      onJobTypesChange([...selectedJobTypes, type]);
    }
  };

  const toggleLocation = (loc: string) => {
    if (selectedLocations.includes(loc)) {
      onLocationsChange(selectedLocations.filter((l) => l !== loc));
    } else {
      onLocationsChange([...selectedLocations, loc]);
    }
  };

  return (
    <aside className="w-full md:w-64 bg-card rounded-lg p-4 border border-slate-700 space-y-4">
      <div>
        <label className="block text-sm font-semibold mb-1">Search</label>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchTermChange(e.target.value)}
          placeholder="Filter by title or company"
          className="w-full px-3 py-2 rounded-md bg-background border border-slate-600 text-sm focus:outline-none focus:border-primary"
        />
      </div>

      <div>
        <span className="block text-sm font-semibold mb-1">Job type</span>
        <div className="space-y-1">
          {jobTypes.map((type) => (
            <label key={type} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={selectedJobTypes.includes(type)}
                onChange={() => toggleJobType(type)}
              />
              <span>{type}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <span className="block text-sm font-semibold mb-1">Location</span>
        <div className="max-h-40 overflow-y-auto space-y-1 text-sm">
          {locations.map((loc) => (
            <label key={loc} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedLocations.includes(loc)}
                onChange={() => toggleLocation(loc)}
              />
              <span>{loc}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1">Date posted</label>
        <select
          value={dateFilter}
          onChange={(e) => onDateFilterChange(e.target.value)}
          className="w-full px-3 py-2 rounded-md bg-background border border-slate-600 text-sm focus:outline-none focus:border-primary"
        >
          <option value="any">Any time</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1">Sort by</label>
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value)}
          className="w-full px-3 py-2 rounded-md bg-background border border-slate-600 text-sm focus:outline-none focus:border-primary"
        >
          <option value="date">Date posted (newest first)</option>
          <option value="alpha">Alphabetical (A-Z)</option>
          <option value="score">AI Score (highest first)</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={savedOnly}
          onChange={(e) => onSavedOnlyChange(e.target.checked)}
        />
        <span className="text-sm">Saved jobs only</span>
      </div>

      <button
        type="button"
        onClick={onClearFilters}
        className="w-full mt-2 px-3 py-2 text-sm font-semibold rounded-md border border-slate-600 hover:border-primary hover:text-primary"
      >
        Clear filters
      </button>
    </aside>
  );
};

export default FilterBar;

