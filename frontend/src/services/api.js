import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Your FastAPI backend URL

export const chatAPI = {
  // Regular query endpoint
  async sendMessage(query, maxSources = 3) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          max_sources: maxSources,
          stream: false
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  // Streaming endpoint for real-time responses
  async streamMessage(query, maxSources = 3, onToken, onSources, onError, onDone) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          max_sources: maxSources,
          stream: true
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'token':
                  onToken && onToken(data.content);
                  break;
                case 'sources':
                  onSources && onSources(data.sources);
                  break;
                case 'error':
                  onError && onError(data.error);
                  break;
                case 'done':
                  onDone && onDone();
                  break;
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error with streaming:', error);
      onError && onError(error.message);
    }
  }
};