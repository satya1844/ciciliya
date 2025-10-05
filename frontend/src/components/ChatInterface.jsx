import React, { useState, useEffect, useRef } from "react";
import { chatAPI } from "../services/api";
import { useDarkMode } from "../contexts/DarkModeContext";
import Loader from "./Loader";
import DarkModeToggle from "./darkModeToggleButton";
import ReactMarkdown from 'react-markdown';
function ChatInterface() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true); // Toggle for streaming
  
  // Use global dark mode context
  const { isDarkMode } = useDarkMode();

  // Ref for the messages container
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Also scroll during streaming (when text is being updated)
  useEffect(() => {
    const streamingMessage = messages.find((msg) => msg.isStreaming);
    if (streamingMessage) {
      scrollToBottom();
    }
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
          // Use streaming for real-time response
          await handleStreamingResponse(currentMessage);
        } else {
          // Use regular API call
          await handleRegularResponse(currentMessage);
        }
      } catch (error) {
        console.error("Chat error:", error);
        addErrorMessage(
          "Sorry, I couldn't process your request. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleRegularResponse = async (query) => {
    try {
      const response = await chatAPI.sendMessage(query);

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
    // Create a placeholder message for streaming
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
      3, // max_sources
      // onToken callback
      (token) => {
        streamedText += token;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMessageId ? { ...msg, text: streamedText } : msg
          )
        );
      },
      // onSources callback
      (sources) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMessageId ? { ...msg, sources: sources } : msg
          )
        );
      },
      // onError callback
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
      // onDone callback
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
      {/* Dark Mode Toggle - Top Right */}
      <div className="absolute top-4 right-2 z-50">
        <DarkModeToggle />
      </div>
      {/* Display messages */}
      <div
        ref={messagesContainerRef}
        className={`absolute w-[759px] h-[350px] pt-10 overflow-y-auto mx-0 scrollbar-hide top-[65px] transition-colors duration-300 ${ 
          isDarkMode ? 'bg-transparent' : 'bg-transparent'
        }`}
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {messages.map((msg) => (
          <div key={msg.id} className="mb-3">
            {msg.sender === "bot" ? (
              <div className="flex items-start">
                {/* Chatbot Avatar - Show loader only when streaming but no text yet */}
                <div className="mr-1 mt-1 flex-shrink-0">
                  {(msg.isStreaming && !msg.text.trim()) || (isLoading && !msg.text.trim()) ? (
                    <Loader />
                  ) : (
                    <div className="w-5 h-5 bg-blue-600 rounded-full"></div>
                  )}
                </div>
                {/* Bot message bubble */}
                <div className={`rounded-xl break-words text-left w-[90%] rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] ${
                  isDarkMode ? 'text-white' : 'text-black'
                } ${msg.text.trim() ? 'p-3' : 'pt-1'}`}>
                  <div className="text-base">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                    {msg.isStreaming && <span className="animate-pulse text-blue-500 ml-1">▋</span>}
                  </div>
                  
                  {/* Display sources if available */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className={`mt-2 pt-2 border-t ${isDarkMode ? 'border-white/20' : 'border-gray-300'}`}>
                      <p className="text-sm opacity-75 mb-1">Sources:</p>
                      {msg.sources.map((source, index) => (
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
            ) : (
              /* User message - no avatar needed */
              <div
                className="p-3 rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] px-4 bg-[#0057FF] text-white ml-auto text-right w-fit"
              >
                <p className="text-base">{msg.text}</p>
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator for initial loading */}
        {isLoading && messages.length > 0 && !messages[messages.length - 1].isStreaming && (
          <div className="mb-3 flex items-start">
            <div className="mr-1 mt-1 flex-shrink-0">
              <Loader />
            </div>
            <div className={`rounded-xl break-words text-left w-[90%] p-3 rounded-tl-[30px] rounded-bl-[30px] rounded-br-[30px] ${
              isDarkMode ? 'text-white/70' : 'text-gray-600'
            }`}>
              <span className={`text-base ${isDarkMode ? 'text-white/70' : 'text-gray-600'}`}>Thinking...</span>
            </div>
          </div>
        )}

        {/* Invisible element to scroll to */}
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
