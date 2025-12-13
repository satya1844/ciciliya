import React, { useState, useEffect, useRef } from "react";
import { chatAPI } from "../services/api";
import Loader from "./Loader";
import MessageBubble from "./MessageBubble";
import grainyTexture from "../styles/grainy.png";
const CubeIcon = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 32 32"
    xmlns="http://www.w3.org/2000/svg"
    className="h-8 w-8 text-white"
  >
    <path
      d="M16 3.5 4.5 9.5v13l11.5 6 11.5-6v-13Z"
      fill="currentColor"
      opacity="0.12"
    />
    <path
      d="M16 3.5 4.5 9.5l11.5 6 11.5-6Z"
      fill="currentColor"
    />
    <path
      d="m16 28.5 11.5-6v-13L16 15.5v13Z"
      fill="currentColor"
      opacity="0.28"
    />
    <path
      d="m16 28.5-11.5-6v-13L16 15.5v13Z"
      fill="currentColor"
      opacity="0.44"
    />
  </svg>
);

const ArrowIcon = ({ className = "h-5 w-5" }) => (
  <svg
    aria-hidden="true"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="m6.75 17.25 6.5-6.5-6.5-6.5M10 10.75h7.25"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.75"
    />
  </svg>
);

function ChatInterface() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useStreaming] = useState(true);

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const hasStreamingMessage = messages.some((msg) => msg.isStreaming);

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
    <section
      className="page relative flex min-h-screen w-full items-center justify-center overflow-hidden px-6 py-16 text-white"
      style={{
        backgroundImage: `url(${grainyTexture})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.08),_transparent_58%)]"
      />
     

     

      <div className="relative z-10 w-full max-w-4xl space-y-10">
        

              <div
                ref={messagesContainerRef}
                className="flex max-h-[60vh] flex-col gap-4 overflow-y-auto pr-2"
              >
                
                {messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    message={cleanMarkdownText(msg.text)}
                    isUser={msg.sender === "user"}
                    sources={msg.sources}
                  />
                ))}
                {isLoading && !hasStreamingMessage && (
                  <div className="flex justify-center py-4">
                    <Loader />
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <form className="w-full" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-interface-input">
            Ask anything
          </label>
          <div className="flex items-center rounded-[36px] border border-white/12 bg-[#030303] px-6 py-4 shadow-[0_24px_52px_rgba(0,0,0,0.45)] backdrop-blur-md sm:px-8 sm:py-5">
            <input
              id="chat-interface-input"
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="lezz goooo..."
              className="flex-1  text-sm text-white placeholder-white/60 outline-none md:text-base"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !message.trim()}
              className="ml-4 flex h-12 w-12 items-center justify-center rounded-full bg-white text-[#362932] transition hover:bg-[#f4f1ff] focus-visible:outline-offset-2 focus-visible:outline-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="sr-only">Send message</span>
              {isLoading ? (
                <ArrowIcon className="h-5 w-5 animate-pulse" />
              ) : (
                <ArrowIcon />
              )}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

export default ChatInterface;