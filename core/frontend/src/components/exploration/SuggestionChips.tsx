import React from 'react';

interface SuggestionChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  disabled?: boolean;
}

export const SuggestionChips: React.FC<SuggestionChipsProps> = ({ 
  suggestions, 
  onSelect, 
  disabled 
}) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => onSelect(suggestion)}
          disabled={disabled}
          className={`
            px-4 py-2 rounded-full text-sm font-medium transition-colors
            border-2 border-blue-100 bg-blue-50 text-blue-700
            hover:bg-blue-100 hover:border-blue-200
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
};
