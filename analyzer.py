import hashlib

def calculate_hash(text):
    """Calculate SHA256 hash of the text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def detect_change(old_hash, new_hash):
    """Return True if hashes are different."""
    return old_hash != new_hash

from openai import OpenAI

def summarize_text(text, api_key=None):
    """
    Generate a summary of the text using OpenAI API.
    """
    if not text:
        return "No content."
    
    if not api_key:
        # Fallback to simple stats if no key provided
        preview = text[:200].replace('\n', ' ')
        word_count = len(text.split())
        return f"Preview: {preview}...\n(Total words: {word_count})\n[Tip: Add OpenAI API Key for AI Summary]"

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes web page content concisely."},
                {"role": "user", "content": f"Please provide a concise summary of the following website content:\n\n{text[:10000]}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Summary Failed: {str(e)}"

def generate_master_summary(page_summaries, api_key=None):
    """
    Generate a master summary from a list of page summaries.
    """
    if not page_summaries:
        return "No content to summarize."
    
    if not api_key:
        return "Master Summary: [Add API Key to generate]"

    combined_text = "\n\n".join(page_summaries)
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You will be given summaries of multiple pages from a single website. Your job is to create a cohesive 'Master Summary' that describes what this website is about and what information it contains based on these page summaries."},
                {"role": "user", "content": f"Here are the summaries of the pages on the website:\n\n{combined_text[:15000]}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Master Summary Failed: {str(e)}"
        return f"Master Summary Failed: {str(e)}"

# Alias for compatibility
summarize = summarize_text

def chat_with_content(content, query, api_key):
    """
    Answer a question based on the provided content (RAG-lite).
    """
    if not api_key:
        return "Error: API Key required for chat."
        
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer the user's question based ONLY on the provided website content. If the answer is not in the content, say so."},
                {"role": "user", "content": f"Context:\n{content[:20000]}\n\nQuestion: {query}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Chat Error: {str(e)}"
