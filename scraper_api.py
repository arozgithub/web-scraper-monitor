"""
Simple REST API wrapper for web scraping - designed for n8n integration.
No MCP dependency required - just a clean HTTP API.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import scraper
import analyzer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/scrape', methods=['POST'])
def scrape_url():
    """
    Scrape a single URL and return content + optional summary.
    
    Request body:
    {
        "url": "https://example.com",
        "api_key": "sk-...", // Optional for AI summary
        "render_js": true,   // Optional: Use Headless Browser
        "use_proxy": true    // Optional: Use Proxy rotation
    }
    """
    data = request.json
    url = data.get('url')
    api_key = data.get('api_key')
    render_js = data.get('render_js', False)
    use_proxy = data.get('use_proxy', False)
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        # Fetch the page
        html, content_type = scraper.fetch_page(url, render_js=render_js, use_proxy=use_proxy)
        if not html:
            return jsonify({"error": "Failed to fetch URL", "url": url}), 400
        
        # Extract text
        text = scraper.extract_text(html, content_type)
        content_hash = analyzer.calculate_hash(text)
        
        # Generate summary if API key provided
        summary = None
        if api_key:
            summary = analyzer.summarize(text, api_key)
        
        result = {
            "success": True,
            "url": url,
            "content_type": content_type,
            "content_hash": content_hash,
            "text_length": len(text),
            "text_preview": text[:500] + "..." if len(text) > 500 else text,
            "full_text": text,
            "summary": summary,
            "rendered_js": render_js
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "url": url}), 500


@app.route('/scrape-complete', methods=['POST'])
def scrape_complete():
    """
    Complete scraping like the UI - crawls entire site and returns all page data.
    
    Request body:
    {
        "url": "https://example.com",
        "max_pages": 50,        // Optional
        "api_key": "sk-...",    // Optional
        "render_js": true,      // Optional
        "use_proxy": true       // Optional
    }
    """
    data = request.json
    root_url = data.get('url') or data.get('root_url')
    api_key = data.get('api_key')
    max_pages = data.get('max_pages', 50)
    render_js = data.get('render_js', False)
    use_proxy = data.get('use_proxy', False)
    
    if not root_url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        # Crawl the website
        pages_data = []
        visited = set()
        to_visit = [root_url]
        
        while to_visit and len(visited) < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            
            visited.add(current_url)
            
            # Fetch and process page
            html, content_type = scraper.fetch_page(current_url, render_js=render_js, use_proxy=use_proxy)
            if not html:
                continue
            
            # Extract text
            text = scraper.extract_text(html, content_type)
            content_hash = analyzer.calculate_hash(text)
            
            pages_data.append({
                "url": current_url,
                "content_hash": content_hash,
                "text_length": len(text),
                "full_text": text
            })
            
            # Find new links to visit
            if content_type and 'html' in content_type.lower():
                internal_links = scraper.get_internal_links(current_url, html, content_type)
                for link in internal_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
        
        result = {
            "success": True,
            "root_url": root_url,
            "pages_crawled": len(pages_data),
            "pages": pages_data
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "root_url": root_url}), 500


@app.route('/crawl', methods=['POST'])
def crawl_website():
    """
    Crawl a website starting from a root URL.
    
    Request body:
    {
        "root_url": "https://example.com",
        "max_pages": 50,
        "api_key": "sk-..." // Optional
    }
    """
    data = request.json
    root_url = data.get('root_url')
    max_pages = data.get('max_pages', 50)
    api_key = data.get('api_key')
    
    if not root_url:
        return jsonify({"error": "root_url is required"}), 400
    
    try:
        # Crawl the website
        pages_data = []
        visited = set()
        to_visit = [root_url]
        
        while to_visit and len(visited) < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            
            visited.add(current_url)
            
            # Fetch and process page
            html, content_type = scraper.fetch_page(current_url)
            if not html:
                continue
            
            text = scraper.extract_text(html, content_type)
            content_hash = analyzer.calculate_hash(text)
            
            # Generate summary if API key provided
            summary = None
            if api_key:
                summary = analyzer.summarize(text, api_key)
            
            pages_data.append({
                "url": current_url,
                "content_hash": content_hash,
                "text_length": len(text),
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "summary": summary
            })
            
            # Find new links to visit
            if content_type and 'html' in content_type.lower():
                internal_links = scraper.get_internal_links(current_url, html, content_type)
                for link in internal_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)


        
        result = {
            "success": True,
            "root_url": root_url,
            "pages_crawled": len(pages_data),
            "pages": pages_data
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "root_url": root_url}), 500


@app.route('/extract-links', methods=['POST'])
def extract_links():
    """
    Extract all internal links from a URL.
    
    Request body:
    {
        "url": "https://example.com"
    }
    """
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        html, content_type = scraper.fetch_page(url)
        if not html:
            return jsonify({
                "success": False,
                "error": "Failed to fetch URL",
                "url": url
            }), 400
        
        # Check if it's HTML (be more lenient with content type)
        is_html = 'html' in content_type.lower() if content_type else True
        if not is_html and not html.strip().startswith('<!DOCTYPE') and not html.strip().startswith('<html'):
            return jsonify({
                "success": False,
                "error": "Not an HTML page",
                "url": url,
                "content_type": content_type
            }), 400
        
        links = scraper.get_internal_links(url, html, content_type or 'text/html')
        
        result = {
            "success": True,
            "url": url,
            "links_found": len(links),
            "links": links
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "url": url}), 500




@app.route('/detect-content-type', methods=['POST'])
def detect_content_type():
    """
    Detect content type of a URL.
    
    Request body:
    {
        "url": "https://example.com/feed.xml"
    }
    """
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        html, content_type = scraper.fetch_page(url)
        
        result = {
            "success": True,
            "url": url,
            "content_type": content_type,
            "is_html": content_type == "html",
            "is_xml": content_type == "xml"
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "url": url}), 500


@app.route('/chat', methods=['POST'])
def chat_with_site():
    """
    Chat with a website content (RAG).
    
    Request body:
    {
        "url": "https://example.com", # Optional (will scrape if provided)
        "content": "...",             # Optional (if you already have text)
        "query": "What is the pricing?",
        "api_key": "sk-..."
    }
    """
    data = request.json
    url = data.get('url')
    content = data.get('content')
    query = data.get('query')
    api_key = data.get('api_key')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    if not api_key:
        return jsonify({"error": "API Key is required"}), 400
        
    try:
        # If URL provided but no content, scrape it first
        if url and not content:
            html, content_type = scraper.fetch_page(url, render_js=True) # Use JS render for best content
            if html:
                content = scraper.extract_text(html, content_type)
        
        if not content:
            return jsonify({"error": "No content provided and failed to scrape URL"}), 400
            
        answer = analyzer.chat_with_content(content, query, api_key)
        
        return jsonify({
            "success": True,
            "query": query,
            "answer": answer
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    """
    Take a screenshot of a URL using Headless Browser.
    
    Request body:
    {
        "url": "https://example.com",
        "use_proxy": true // Optional
    }
    """
    data = request.json
    url = data.get('url')
    use_proxy = data.get('use_proxy', False)
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    try:
        from scraper import fetch_page_playwright
        
        content, content_type, screenshot_path = fetch_page_playwright(url, use_proxy=use_proxy, save_screenshot=True)
        
        if screenshot_path:
            # Construct full URL
            base_url = request.host_url.rstrip('/')
            screenshot_url = f"{base_url}/static/screenshots/{screenshot_path}"
            
            return jsonify({
                "success": True,
                "url": url,
                "screenshot_url": screenshot_url,
                "screenshot_path": screenshot_path
            })
        else:
            return jsonify({"success": False, "error": "Failed to take screenshot"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/diff', methods=['POST'])
def generate_diff():
    """
    Generate a visual HTML diff between two text blocks.
    """
    data = request.json
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    
    import difflib
    d = difflib.HtmlDiff()
    # Generate HTML diff
    html_diff = d.make_file(text1.splitlines(), text2.splitlines(), context=True, numlines=2)
    
    return html_diff

@app.route('/linkedin-scrape', methods=['POST'])
def linkedin_scrape():
    """
    Scrape LinkedIn profile or company page using saved session.
    
    Request body:
    {
        "url": "https://www.linkedin.com/in/...",
        "headless": true // Optional (default: true)
    }
    """
    data = request.json
    url = data.get('url')
    headless = data.get('headless', True)
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    try:
        import linkedin_scraper
        result = linkedin_scraper.scrape_linkedin_page(url, headless=headless)
        
        if "error" in result:
            return jsonify({"success": False, "error": result['error']}), 400
            
        return jsonify({"success": True, "data": result})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "web-scraper-api",
        "version": "1.0.0"
    })


@app.route('/info', methods=['GET'])
def get_info():
    """Get API information and available endpoints."""
    return jsonify({
        "service": "Web Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "/scrape": {
                "method": "POST",
                "description": "Scrape a single URL",
                "params": {"url": "required", "api_key": "optional"}
            },
            "/scrape-complete": {
                "method": "POST",
                "description": "Complete scraping - crawls entire site and returns all page data with full text",
                "params": {"url": "required", "max_pages": "optional (default: 50)"}
            },
            "/crawl": {
                "method": "POST",
                "description": "Crawl entire website",
                "params": {"root_url": "required", "max_pages": "optional (default: 50)", "api_key": "optional"}
            },
            "/extract-links": {
                "method": "POST",
                "description": "Extract links from a URL",
                "params": {"url": "required"}
            },
            "/detect-content-type": {
                "method": "POST",
                "description": "Detect content type",
                "params": {"url": "required"}
            },
            "/health": {
                "method": "GET",
                "description": "Health check"
            },
            "/info": {
                "method": "GET",
                "description": "API information"
            }
        },
        "features": [
            "HTML scraping with BeautifulSoup",
            "XML parsing support",
            "Automatic content type detection",
            "Internal link extraction",
            "Website crawling with depth control",
            "Content hashing for change detection",
            "AI-powered summarization (with OpenAI API key)"
        ]
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🌐 Web Scraper API Server")
    print("=" * 60)
    print("Starting server on http://localhost:5001")
    print("Available endpoints:")
    print("  POST /scrape              - Scrape single URL")
    print("  POST /scrape-complete     - Complete scraping (crawl all pages + return full text)")
    print("  POST /crawl               - Crawl entire website")
    print("  POST /chat                - Chat with website content (RAG)")
    print("  POST /screenshot          - Take screenshot (Headless Browser)")
    print("  POST /extract-links       - Extract links from URL")
    print("  POST /detect-content-type - Detect content type")
    print("  GET  /health              - Health check")
    print("  GET  /info                - API information")
    print("\nReady for n8n integration!")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
