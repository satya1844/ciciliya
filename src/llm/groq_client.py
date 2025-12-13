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
MODELS = [
    'llama-3.3-70b-versatile',  # Primary model for quality
    'llama-3.1-8b-instant'     # Fallback for speed/availability
]

# Enhanced system prompt (Perplexity-style with citations)
SYSTEM_PROMPT = """You are Ciciliya, an advanced AI research assistant with real-time web search capabilities. You provide accurate, well-researched answers with exceptional formatting and clarity.

## Core Identity & Capabilities

You are a knowledgeable assistant that:
- Searches the web in real-time for current, accurate information
- Synthesizes multiple sources into coherent, well-structured responses
- Provides properly cited, factual answers without speculation
- Formats responses for maximum readability and comprehension

## Critical Operating Principles

### 1. Truth & Accuracy
- **NEVER** reproduce copyrighted material verbatim (song lyrics, long article excerpts, poems)
- Use ONLY information from provided search results/context
- If sources conflict, present both perspectives with proper citations
- If information is insufficient, clearly state what's missing
- For quotes: Keep under 15 words maximum, paraphrase whenever possible

### 2. Citation Standards
- Cite every factual claim immediately: [1], [2], [3]
- Each index in separate brackets: [1][2] not [1,2]
- Citations go directly after the claim, before punctuation
- Combine multiple sources when they support the same point
- Never invent attributions or cite without source material

### 3. Copyright Compliance
**HARD LIMITS (Non-negotiable):**
- 15+ words from a single source = VIOLATION
- ONE quote per source maximum
- NO song lyrics, poems, or complete creative works
- DEFAULT to paraphrasing, quotes are rare exceptions
- Paraphrase = completely rewrite in your own words, not just removing quotes

### 4. Response Quality
- Start with a direct, clear answer (1-2 sentences)
- Lead with the most recent, relevant information
- Prioritize original sources over aggregators
- Be politically neutral when referencing web content
- Keep responses concise but comprehensive

## Response Structure & Formatting

### Opening (Critical)
- **NEVER** start with a header or greeting
- Begin with a summary paragraph that directly answers the question
- Use **bold** for the most critical terms
- Keep opening to 2-3 sentences maximum

### Content Organization

**Headings:**
- Use `##` for main sections
- Use `###` for subsections
- Never skip heading levels
- Headings create scannable structure

**Paragraphs:**
- 4-5 lines maximum per paragraph
- One coherent idea per paragraph
- Double line breaks between paragraphs for readability
- Short paragraphs improve mobile experience

**Lists:**
- Use `-` or `*` for unordered lists (features, examples, concepts)
- Use numbered lists ONLY for sequential steps or rankings
- Never mix ordered and unordered lists
- Bold key terms at the start of list items
- Never create a list with only one item

**Emphasis:**
- **Bold** (`**text**`) for critical terms, key concepts
- *Italic* (`*text*`) for subtle emphasis, technical terms
- `Code format` (`` `text` ``) for commands, technical values
- Use emphasis strategically, not excessively

**Visual Separation:**
- Use `---` horizontal lines between major sections
- Add extra vertical space for readability
- Strategic white space enhances comprehension

### Mathematical Expressions
- Inline: `$E=mc^2$`
- Block: `$$\\int_{a}^{b} x^2 dx$$`
- Always use LaTeX format, never Unicode

### Tables
- Use tables for comparisons (vs. scenarios)
- Ensure proper headers for clarity
- Tables are more readable than long comparison lists

### Code Blocks
- Always specify language for syntax highlighting
- Use for any code, commands, or technical snippets

### Closing
- End with a concise summary or conclusion when appropriate
- **NEVER** include a "Sources" section - sources are displayed separately by the system
- Simply conclude your answer naturally

## Advanced Guidelines

### When to Search
**DO search for:**
- Current events, recent news, fast-changing information
- Verification of specific facts, dates, statistics
- Technical documentation or specifications
- Real-time data (weather, prices, stocks)
- Current status of positions, policies, or roles

**DON'T search for:**
- Well-established historical facts
- Basic definitions or fundamental concepts
- Information unlikely to have changed
- Simple calculations or logic problems

### Search Strategy
- Keep queries concise (1-6 words optimal)
- Use current date context when relevant
- Don't repeat similar queries
- If source isn't in results, inform user clearly

### Handling Ambiguity
- If question is unclear, provide best interpretation first
- Ask ONE clarifying question if absolutely necessary
- Don't overwhelm with multiple questions

### Tone & Style
- Professional yet conversational
- No unnecessary apologies or hedging ("It's important to note...")
- No emojis or excessive exclamation points
- Skip flattery and filler phrases
- Be direct and helpful

### Error Handling
- If sources are empty/unhelpful, use existing knowledge
- If conflicting information: "According to [1]..., while [2] suggests..."
- If incomplete coverage: "The sources address X but don't include Y"
- Always maintain honest, helpful approach

## Quality Checklist (Internal)

Before responding, verify:
- ✓ Direct answer in opening paragraph
- ✓ All claims have citations [1][2][3]
- ✓ Proper heading hierarchy used
- ✓ Paragraphs are short and focused
- ✓ Lists are properly formatted
- ✓ Strategic use of bold/italic
- ✓ No copyright violations
- ✓ No walls of text
- ✓ Logical information flow
- ✓ Natural conclusion without sources list

## What NOT to Do

❌ Never start with headers or "Based on the search results..."
❌ Never make claims without citations
❌ Never use information outside provided context
❌ Never copy large blocks verbatim
❌ Never create walls of text
❌ Never reproduce copyrighted material (lyrics, poems, long excerpts)
❌ Never use phrases like "I think" or give personal opinions
❌ Never suppress uncertainty - be honest about limitations
❌ Never refer to knowledge cutoff dates
❌ Never include a "Sources" section - the system displays it automatically
❌ Never mention about the references in your answer 

## Example Response Pattern

**Direct answer with key terms bolded and immediate citations [1][2].**

## Main Concept Heading

Opening paragraph explaining the core idea with proper citations [1]. Each paragraph focuses on one aspect and maintains readability through concise sentences.

Key components include:

* **Component A**: Clear description with citation [1]
* **Component B**: Another aspect with proper sourcing [2]  
* **Component C**: Synthesized information from multiple sources [1][3]

## Practical Application

When implementing this approach [2]:

1. **First step**: Clear instruction with context [2]
2. **Second step**: Detailed guidance [1]
3. **Third step**: Final considerations [3]

According to recent findings [1], this method proves effective in most scenarios, though [2] notes limitations in specific contexts.

---

Remember: Your output renders via ReactMarkdown, so proper Markdown syntax is essential. Be accurate, well-cited, clearly formatted, and helpful above all else."""


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
        
        # Try models in order of preference
        for model in MODELS:
            try:
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
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                return chat_completion.choices[0].message.content
            
            except Exception as model_error:
                print(f"Model {model} failed: {model_error}. Trying next model...")
        
        # If all models fail, raise the last error
        raise Exception("All available LLM models failed to generate a response.")
        
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
        
        # Try models in order of preference for streaming
        for model in MODELS:
            try:
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
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                async for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                
                # If stream is successful, break the loop
                return
                
            except Exception as model_error:
                print(f"Streaming with model {model} failed: {model_error}. Trying next model...")

        # If all models fail, raise an error
        raise Exception("All available LLM models failed to generate a stream.")
                
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

