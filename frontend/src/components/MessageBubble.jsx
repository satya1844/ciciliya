import React from 'react';
import ReactMarkdown from 'react-markdown';

import { useDarkMode } from '../contexts/DarkModeContext';

const MessageBubble = ({ message, isUser, sources }) => {
  const { isDarkMode } = useDarkMode();
  const markdownClass = isDarkMode
    ? 'markdown-content markdown-content-dark'
    : 'markdown-content markdown-content-light';

  if (isUser) {
    const formattedMessage = (
      <div className="prose prose-neutral max-w-none">
      <ReactMarkdown>
        {message}
      </ReactMarkdown>
      </div>
    );

    return (
      <div className="p-3 rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] px-4  text-white ml-auto text-right w-fit">
        {formattedMessage}
      </div>
    );
  }

  return (
    <div className="flex items-start">
      <div
        className={`rounded-xl text-xl break-words text-left w-[90%] p-5 rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] `}
      ><div className="markdown-content-wrapper">

      
        <ReactMarkdown>
          {message}
        </ReactMarkdown>
        </div>
        
        {/* Display sources if available */}
        {sources && sources.length > 0 && (
          <div className={`mt-2 pt-2 border-t ${isDarkMode ? 'border-white/20' : 'border-gray-300'}`}>
            <p className="text-sm opacity-75 mb-1">Sources:</p>
            {sources.map((source, index) => (
              <div key={index} className="text-xs mb-1">
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`underline ${isDarkMode ? 'text-blue-300 hover:text-blue-200' : 'text-blue-600 hover:text-blue-800'}`}
                >
                  {source.title}
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
