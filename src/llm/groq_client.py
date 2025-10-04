import os
from groq import AsyncGroq
from typing import AsyncGenerator, List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

# Use llama-3.1-70b-versatile for better quality responses
# or llama-3.1-8b-instant for faster responses
MODEL = 'llama-3.3-70b-versatile'  # Changed for better quality

# Enhanced system prompt (Perplexity-style with citations)
SYSTEM_PROMPT = """You are an advanced AI research assistant with real-time web access, designed to provide accurate, well-researched answers.

## Your Mission:
Answer questions accurately using ONLY the provided sources. Think of yourself as a knowledgeable researcher who synthesizes information from multiple sources.

## Core Rules:
1. **Cite Everything**: Use [1], [2], [3] format immediately after each claim
2. **Be Direct**: Start with a clear answer, then elaborate with details
3. **Stay Grounded**: Only use information from the provided CONTEXT
4. **Synthesize**: Combine information from multiple sources into a coherent narrative
5. **Be Honest**: If sources don't fully answer the question, clearly state what's missing

## Response Format:
- Begin with a direct answer (1-2 sentences)
- Elaborate with supporting details from sources [1][2][3]
- Use citations [1] right after each factual claim
- If sources conflict, present both views: "According to [1]... while [2] suggests..."
- End with: "\n\nSources:\n[1] Title - URL\n[2] Title - URL"

## Quality Guidelines:
- Write naturally and conversationally
- Explain technical terms simply
- Cross-reference multiple sources when possible
- If information is insufficient: "The sources cover X, but don't include information about Y"
- For current events, mention dates: "As of [date]..."
- Never fabricate or hallucinate information

## What NOT to Do:
❌ Never make claims without citations
❌ Never use information outside the provided context
❌ Never say "I think" or give personal opinions
❌ Never copy large blocks verbatim - synthesize and paraphrase"""


def format_sources_for_context(sources: List[Dict]) -> str:
    """
    Format sources into a structured context string with numbered citations.
    
    Args:
        sources: List of dicts with 'title', 'url', 'content'/'text' keys
    
    Returns:
        Formatted context string with numbered sources
    """
    if not sources:
        return "No sources available."
    
    context_parts = []
    for idx, source in enumerate(sources, 1):
        title = source.get('title', 'Untitled')
        url = source.get('url', 'N/A')
        content = source.get('content') or source.get('text', '')
        
        # Truncate very long content to stay within token limits
        max_content_length = 3000  # characters per source
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        context_parts.append(
            f"[{idx}] {title}\n"
            f"URL: {url}\n"
            f"Content: {content}\n"
            f"---"
        )
    
    return "\n\n".join(context_parts)


def build_prompt(query: str, context: str, use_concise: bool = False) -> str:
    """
    Build the complete prompt for the LLM.
    
    Args:
        query: User's question
        context: Formatted context string with sources
        use_concise: If True, use shorter prompt (faster but less detailed)
    
    Returns:
        Complete formatted prompt
    """
    if use_concise:
        # Shorter prompt for faster responses
        return f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

USER QUESTION:
{query}

Provide a well-cited answer now:"""
    else:
        # Full prompt for comprehensive responses
        return f"""{SYSTEM_PROMPT}

---
CONTEXT (Retrieved Sources):
{context}
---

USER QUESTION:
{query}

Now provide a comprehensive, well-cited answer based solely on the information in the CONTEXT above. Remember to cite every claim with [1], [2], [3] and list sources at the end."""


async def get_groq_response(
    user_prompt: str, 
    context: str = None,
    sources: List[Dict] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    use_concise: bool = False
) -> str:
    """
    Generates a response from the Groq model with enhanced prompting.
    
    Args:
        user_prompt: The user's question
        context: Pre-formatted context string (optional if sources provided)
        sources: List of source dicts to format (optional if context provided)
        temperature: Controls randomness (0.0-1.0). Lower = more factual
        max_tokens: Maximum response length
        use_concise: Use shorter prompt for faster responses
    
    Returns:
        The model's response as a string
    """
    try:
        # Format sources if provided
        if sources and not context:
            context = format_sources_for_context(sources)
        elif not context:
            context = "No sources available."
        
        # Build the enhanced prompt
        full_prompt = build_prompt(user_prompt, context, use_concise)
        
        # Use system/user message structure (more reliable)
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""CONTEXT:
{context}

QUESTION:
{user_prompt}

Provide a comprehensive, well-cited answer:"""
                }
            ],
            model=MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        print(f"Groq LLM error: {e}")
        raise e


async def get_groq_response_stream(
    user_prompt: str, 
    context: str = None,
    sources: List[Dict] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    use_concise: bool = False
) -> AsyncGenerator[str, None]:
    """
    Streams the response from the Groq model token by token.
    
    Args:
        user_prompt: The user's question
        context: Pre-formatted context string (optional if sources provided)
        sources: List of source dicts to format (optional if context provided)
        temperature: Controls randomness (0.0-1.0). Lower = more factual
        max_tokens: Maximum response length
        use_concise: Use shorter prompt for faster responses
    
    Yields:
        Response tokens as they're generated
    """
    try:
        # Format sources if provided
        if sources and not context:
            context = format_sources_for_context(sources)
        elif not context:
            context = "No sources available."
        
        # Build the enhanced prompt
        full_prompt = build_prompt(user_prompt, context, use_concise)
        
        # Stream with system/user messages
        stream = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""CONTEXT:
{context}

QUESTION:
{user_prompt}

Provide a comprehensive, well-cited answer:"""
                }
            ],
            model=MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
                
    except Exception as e:
        print(f"Groq LLM streaming error: {e}")
        raise e


# Convenience function for quick testing
async def test_groq_response():
    """
    Test function to verify Groq integration works.
    """
    test_sources = [
        {
            "title": "Python Programming",
            "url": "https://example.com/python",
            "content": "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991."
        }
    ]
    
    response = await get_groq_response(
        user_prompt="What is Python?",
        sources=test_sources
    )
    
    print("Test Response:")
    print(response)


# Example usage
"""
# In your chat_pipeline.py:

from llm.groq_client import get_groq_response, get_groq_response_stream

# Option 1: Pass pre-formatted context
context = format_sources_for_context(retrieved_sources)
answer = await get_groq_response(user_query, context=context)

# Option 2: Pass sources directly (recommended)
answer = await get_groq_response(
    user_prompt=user_query,
    sources=retrieved_sources,
    temperature=0.3,  # Lower = more factual, higher = more creative
    max_tokens=2048
)

# Option 3: Stream the response
async for token in get_groq_response_stream(user_query, sources=retrieved_sources):
    print(token, end='', flush=True)
"""