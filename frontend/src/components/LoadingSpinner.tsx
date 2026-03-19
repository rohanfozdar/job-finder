import React from "react";

const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center py-4">
      <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      <span className="ml-3 text-sm text-text/80">Searching jobs...</span>
    </div>
  );
};

export default LoadingSpinner;

