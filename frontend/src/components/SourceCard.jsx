import React from 'react';
import { useDarkMode } from '../contexts/DarkModeContext';

const SourceCard = ({ source }) => {
  const { isDarkMode } = useDarkMode();

  return (
    <div className={`p-3 rounded-lg border transition-all duration-200 hover:shadow-md ${
      isDarkMode 
        ? 'bg-white/5 border-white/20 hover:bg-white/10' 
        : 'bg-white border-gray-200 hover:bg-gray-50'
    }`}>
      <h4 className={`font-semibold text-sm mb-1 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>
        {source.title}
      </h4>
      
      {source.snippet && (
        <p className={`text-xs mb-2 line-clamp-3 ${
          isDarkMode ? 'text-gray-300' : 'text-gray-600'
        }`}>
          {source.snippet}
        </p>
      )}
      
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className={`text-xs underline ${
          isDarkMode 
            ? 'text-blue-300 hover:text-blue-200' 
            : 'text-blue-600 hover:text-blue-800'
        }`}
      >
        View Source
      </a>
    </div>
  );
};

export default SourceCard;
