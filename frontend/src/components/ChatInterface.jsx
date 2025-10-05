

import React, { useState, useEffect, useRef } from "react";
import { chatAPI } from "../services/api";
import { useDarkMode } from "../contexts/DarkModeContext";
import Loader from "./Loader";
import DarkModeToggle from "./darkModeToggleButton";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function ChatInterface() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  
  const { isDarkMode } = useDarkMode();
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Helper to clean escaped markdown
  const cleanMarkdownText = (text) => {
    if (!text) return "";
    
    let cleaned = text.trim();
    
    // Remove wrapping quotes if present
    if (cleaned.startsWith('"') && cleaned.endsWith('"')) {
      cleaned = cleaned.slice(1, -1);
    }
    
    // Unescape markdown characters
    cleaned = cleaned
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, '\t')
      .replace(/\\"/g, '"')
      .replace(/\\\*/g, '*')
      .replace(/\\#/g, '#')
      .replace(/\\\[/g, '[')
      .replace(/\\\]/g, ']')
      .replace(/\\\(/g, '(')
      .replace(/\\\)/g, ')')
      .replace(/\\\\/g, '\\');
    
    return cleaned;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      const userMessage = {
        id: Date.now(),
        text: message,
        sender: "user",
      };

      setMessages((prev) => [...prev, userMessage]);
      const currentMessage = message;
      setMessage("");
      setIsLoading(true);

      try {
        if (useStreaming) {
          await handleStreamingResponse(currentMessage);
        } else {
          await handleRegularResponse(currentMessage);
        }
      } catch (error) {
        console.error("Chat error:", error);
        addErrorMessage("Sorry, I couldn't process your request. Please try again.");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleRegularResponse = async (query) => {
    try {
      const response = await chatAPI.sendMessage(query);

      // 🔍 DEBUG: Check what we're getting
      console.log("Regular response answer:", JSON.stringify(response.answer));

      const botMessage = {
        id: Date.now() + 1,
        text: response.answer,
        sender: "bot",
        sources: response.sources,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      throw error;
    }
  };

  const handleStreamingResponse = async (query) => {
    const botMessageId = Date.now() + 1;
    let streamedText = "";

    const botMessage = {
      id: botMessageId,
      text: "",
      sender: "bot",
      sources: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, botMessage]);

    await chatAPI.streamMessage(
      query,
      3,
      (token) => {
        streamedText += token;
        
        // 🔍 DEBUG: Check what tokens we're getting
        console.log("Token received:", JSON.stringify(token));
        console.log("Accumulated text so far:", JSON.stringify(streamedText.substring(0, 50)) + "...");
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMessageId ? { ...msg, text: streamedText } : msg
          )
        );
      },
      (sources) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMessageId ? { ...msg, sources: sources } : msg
          )
        );
      },
      (error) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMessageId
              ? {
                  ...msg,
                  text: "Sorry, an error occurred.",
                  isStreaming: false,
                }
              : msg
          )
        );
      },
      () => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMessageId ? { ...msg, isStreaming: false } : msg
          )
        );
      }
    );
  };

  const addErrorMessage = (errorText) => {
    const errorMessage = {
      id: Date.now() + 1,
      text: errorText,
      sender: "bot",
    };
    setMessages((prev) => [...prev, errorMessage]);
  };

  return (
    <div className={`max-w-3xl mx-auto flex justify-center p-5 font-jersey relative transition-colors duration-300 ${
      isDarkMode ? 'text-white' : 'text-black'
    }`}>
      <div className="absolute top-4 right-2 z-50">
        <DarkModeToggle />
      </div>

      <div
        ref={messagesContainerRef}
        className={`absolute w-[759px] h-[350px] pt-10 overflow-y-auto mx-0 scrollbar-hide top-[65px] transition-colors duration-300`}
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {messages.map((msg) => (
          <div key={msg.id} className="mb-3">
            {msg.sender === "bot" ? (
              <div className="flex items-start">
                <div className="mr-1 mt-1 flex-shrink-0">
                  {(msg.isStreaming && !msg.text.trim()) || (isLoading && !msg.text.trim()) ? (
                    <Loader />
                  ) : (
                    <div className="w-5 h-5 bg-blue-600 rounded-full"></div>
                  )}
                </div>
                
                <div className={`rounded-xl break-words text-left w-[90%] rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] ${
                  isDarkMode ? 'text-white' : 'text-black'
                } ${msg.text.trim() ? 'p-3' : 'pt-1'}`}>
                  <div className="text-base markdown-content">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({node, ...props}) => (
                          <p className="mb-3 leading-relaxed last:mb-0" {...props} />
                        ),
                        h2: ({node, ...props}) => (
                          <h2 className="text-xl font-bold mb-2 mt-4 first:mt-0" {...props} />
                        ),
                        h3: ({node, ...props}) => (
                          <h3 className="text-lg font-bold mb-2 mt-3 first:mt-0" {...props} />
                        ),
                        strong: ({node, ...props}) => (
                          <strong className={`font-bold ${isDarkMode ? 'text-blue-300' : 'text-blue-600'}`} {...props} />
                        ),
                        em: ({node, ...props}) => (
                          <em className="italic" {...props} />
                        ),
                        ul: ({node, ...props}) => (
                          <ul className="list-disc list-outside ml-5 mb-3 space-y-1" {...props} />
                        ),
                        ol: ({node, ...props}) => (
                          <ol className="list-decimal list-outside ml-5 mb-3 space-y-1" {...props} />
                        ),
                        li: ({node, ...props}) => (
                          <li className="leading-relaxed" {...props} />
                        ),
                        code: ({node, inline, ...props}) => {
                          if (inline) {
                            return (
                              <code 
                                className={`px-1.5 py-0.5 rounded text-sm font-mono ${
                                  isDarkMode ? 'bg-gray-700 text-green-300' : 'bg-gray-200 text-red-600'
                                }`}
                                {...props}
                              />
                            );
                          }
                          return (
                            <code 
                              className={`block p-3 rounded-md text-sm font-mono overflow-x-auto mb-3 ${
                                isDarkMode ? 'bg-gray-800 text-green-300' : 'bg-gray-100 text-gray-800'
                              }`}
                              {...props}
                            />
                          );
                        },
                        hr: ({node, ...props}) => (
                          <hr className={`my-4 border-t ${isDarkMode ? 'border-gray-600' : 'border-gray-300'}`} {...props} />
                        ),
                        a: ({node, ...props}) => (
                          <a 
                            className={`underline ${isDarkMode ? 'text-blue-300 hover:text-blue-200' : 'text-blue-600 hover:text-blue-800'}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            {...props}
                          />
                        ),
                      }}
                    >
                      {cleanMarkdownText(msg.text)}
                    </ReactMarkdown>
                    {msg.isStreaming && (
                      <span className="inline-block animate-pulse text-blue-500 ml-1">▋</span>
                    )}
                  </div>
                  
                  {msg.sources && msg.sources.length > 0 && (
                    <div className={`mt-3 pt-3 border-t ${isDarkMode ? 'border-white/20' : 'border-gray-300'}`}>
                      <p className="text-sm font-semibold opacity-75 mb-2">Sources:</p>
                      <div className="space-y-1">
                        {msg.sources.map((source, index) => (
                          <div key={index} className="text-xs">
                            <span className="opacity-60">[{index + 1}]</span>{' '}
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`underline ${
                                isDarkMode ? 'text-blue-300 hover:text-blue-200' : 'text-blue-600 hover:text-blue-800'
                              }`}
                            >
                              {source.title}
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] px-4 bg-[#0057FF] text-white ml-auto text-right w-fit">
                <p className="text-base">{msg.text}</p>
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <div className="rounded-3xl p-7 bg-[#0057FF] text-white absolute w-[759px] top-107">
        <form onSubmit={handleSubmit}>
          <h1 className="text-2xl font-bold border border-white p-3 jersey-10-regular rounded-2xl flex justify-between items-center">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask anything.."
              className="keep-blue-bg bg-[#0057FF] border-none outline-none text-white placeholder-cyan-300 flex-1"
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading}>
              <p>{isLoading ? "..." : "Submit"}</p>
            </button>
          </h1>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;