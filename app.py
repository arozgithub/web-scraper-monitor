from flask import Flask, render_template, jsonify, request
import threading
import datetime
import sqlite3
import storage
import scraper
import analyzer
import linkedin_scraper
from scheduler_service import SchedulerService

app = Flask(__name__)

# Global variable to store API Key
OPENAI_API_KEY = None

# Background Scheduler
scheduler = SchedulerService()

# --- Helpers ---
def get_all_pages_grouped():
    return storage.get_pages_grouped()

def crawl_and_scrape(start_url, api_key, capture_screenshots=False):
    """
    Recursively crawl and scrape pages starting from start_url.
    Run this in a background thread.
    """
    print(f"Starting crawl for {start_url} (screenshots: {capture_screenshots})")
    queue = [start_url]
    visited = set()
    MAX_PAGES = 20

    while queue and len(visited) < MAX_PAGES:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        
        print(f"Processing: {url}")
        start_time = datetime.datetime.now().isoformat()
        html, content_type = scraper.fetch_page(url, render_js=capture_screenshots, save_screenshot=capture_screenshots)
        
        if not html:
            storage.log_scrape_run(start_url, url, start_time, datetime.datetime.now().isoformat(), "failed", 0, False)
            continue

        text = scraper.extract_text(html, content_type)
        bytes_fetched = len(html.encode('utf-8'))
        new_hash = analyzer.calculate_hash(text)
        
        summary = analyzer.summarize_text(text, api_key)
        changed = storage.save_page(url, new_hash, summary, text, root_url=start_url)
        storage.log_scrape_run(start_url, url, start_time, datetime.datetime.now().isoformat(), "success", bytes_fetched, changed)
        
        links = scraper.get_internal_links(url, html, content_type)
        for link in links:
            if link not in visited and link not in queue:
                queue.append(link)
    
    print(f"Crawl finished for {start_url}")
    
    # Generate Master Summary
    if api_key:
        print(f"Generating master summary for {start_url}...")
        grouped = storage.get_pages_grouped()
        root_data = grouped.get(start_url)
        
        if root_data:
            summaries = [p['summary'] for p in root_data['pages'] if p['summary']]
            master_summary = analyzer.generate_master_summary(summaries, api_key)
            storage.save_site_summary(start_url, master_summary)
            print(f"Master summary saved for {start_url}")

def perform_scrape_job(url, capture_screenshots=False):
    """Wrapper to run crawl in background."""
    thread = threading.Thread(target=crawl_and_scrape, args=(url, OPENAI_API_KEY, capture_screenshots))
    thread.start()

def reload_schedules():
    """Reload all active schedules from DB."""
    schedules = storage.get_all_schedules()
    for root_url, data in schedules.items():
        if data['active']:
            scheduler.add_job(root_url, data['val'], data['unit'], lambda u=root_url: perform_scrape_job(u, False))
        else:
            scheduler.remove_job(root_url)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pages', methods=['GET'])
def api_get_pages():
    return jsonify(get_all_pages_grouped())

@app.route('/api/pages', methods=['POST'])
def api_add_page():
    data = request.json
    url = data.get('url')
    api_key = data.get('apiKey')
    interval_val = int(data.get('intervalVal', 60))
    interval_unit = data.get('intervalUnit', 'minutes')
    capture_screenshots = data.get('captureScreenshots', False)
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    global OPENAI_API_KEY
    if api_key:
        OPENAI_API_KEY = api_key
    
    perform_scrape_job(url, capture_screenshots)
    
    storage.save_schedule(url, interval_val, interval_unit, True)
    scheduler.add_job(url, interval_val, interval_unit, lambda: perform_scrape_job(url, capture_screenshots))
    
    return jsonify({"success": True, "message": "Started crawling and monitoring..."})

@app.route('/api/schedule/toggle', methods=['POST'])
def api_toggle_schedule():
    data = request.json
    root_url = data.get('root_url')
    is_active = data.get('is_active')
    
    if not root_url:
        return jsonify({"error": "Root URL is required"}), 400
        
    schedules = storage.get_all_schedules()
    if root_url not in schedules:
        return jsonify({"error": "Schedule not found"}), 404
        
    current = schedules[root_url]
    storage.save_schedule(root_url, current['val'], current['unit'], is_active)
    
    if is_active:
        scheduler.add_job(root_url, current['val'], current['unit'], lambda: perform_scrape_job(root_url, False))
    else:
        scheduler.remove_job(root_url)
        
    return jsonify({"success": True, "message": f"Schedule {'activated' if is_active else 'paused'}."})

@app.route('/api/pages', methods=['DELETE'])
def api_delete_page():
    data = request.json
    root_url = data.get('root_url')
    if not root_url:
        return jsonify({"error": "Root URL is required"}), 400
        
    count = storage.delete_root(root_url)
    scheduler.remove_job(root_url)
    return jsonify({"success": True, "message": f"Deleted {count} pages."})

@app.route('/api/scrape', methods=['POST'])
def api_trigger_scrape():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    perform_scrape_job(url, False)
    return jsonify({"success": True, "message": "Scrape triggered in background"})

@app.route('/api/history/<path:url>', methods=['GET'])
def api_get_history(url):
    """Get scrape history for a specific URL."""
    history = storage.get_scrape_history(url, limit=20)
    return jsonify(history)

@app.route('/api/compare-versions', methods=['POST'])
def api_compare_versions():
    """Compare two versions of a monitored URL."""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT scraped_at, content, summary
        FROM scrape_history
        WHERE url = ?
        ORDER BY scraped_at DESC
        LIMIT 2
    ''', (url,))
    
    versions = cursor.fetchall()
    conn.close()
    
    if len(versions) < 2:
        return jsonify({"error": "Need at least 2 versions to compare"}), 400
    
    new_version = {
        "date": versions[0][0],
        "content": versions[0][1] or "",
        "summary": versions[0][2] or ""
    }
    
    old_version = {
        "date": versions[1][0],
        "content": versions[1][1] or "",
        "summary": versions[1][2] or ""
    }
    
    import difflib
    d = difflib.HtmlDiff()
    diff_html = d.make_file(
        old_version['content'].splitlines(),
        new_version['content'].splitlines(),
        fromdesc=f"Version from {old_version['date']}",
        todesc=f"Current version from {new_version['date']}",
        context=True,
        numlines=3
    )
    
    return jsonify({
        "success": True,
        "url": url,
        "old_version": old_version,
        "new_version": new_version,
        "diff_html": diff_html
    })

@app.route('/api/analytics', methods=['GET'])
def api_get_analytics():
    """Get dashboard analytics."""
    time_window = request.args.get('window', '24h')
    try:
        data = storage.get_analytics(time_window)
        return jsonify(data)
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    url = data.get('url')
    query = data.get('query')
    api_key = data.get('apiKey')
    
    if not query or not api_key:
        return jsonify({"error": "Query and API Key are required"}), 400
    
    content_parts = []
    
    if url:
        conn = sqlite3.connect('monitor.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM pages WHERE root_url = ?', (url,))
        page_count = cursor.fetchone()[0]
        
        if page_count > 0:
            cursor.execute('''
                SELECT p.url, p.summary, p.last_scraped, h.content
                FROM pages p
                LEFT JOIN (
                    SELECT url, content
                    FROM scrape_history sh1
                    WHERE scraped_at = (
                        SELECT MAX(scraped_at)
                        FROM scrape_history sh2
                        WHERE sh2.url = sh1.url
                    )
                ) h ON p.url = h.url
                WHERE p.root_url = ?
                ORDER BY p.last_scraped DESC
                LIMIT 50
            ''', (url,))
            
            pages = cursor.fetchall()
            conn.close()
            
            content_parts.append(f"Website Root: {url}")
            content_parts.append(f"Total Pages Monitored: {len(pages)}\n")
            
            for idx, (page_url, summary, last_scraped, content) in enumerate(pages, 1):
                content_parts.append(f"Page {idx}:")
                content_parts.append(f"URL: {page_url}")
                if summary:
                    content_parts.append(f"Summary: {summary}")
                if last_scraped:
                    content_parts.append(f"Last Scraped: {last_scraped}")
                if content:
                    truncated_content = content[:3000]
                    content_parts.append(f"Content Preview: {truncated_content}")
                content_parts.append("")
        else:
            cursor.execute('SELECT url, summary, content_hash FROM pages WHERE url = ? LIMIT 1', (url,))
            page = cursor.fetchone()
            conn.close()
            
            if page:
                content_parts.append(f"URL: {page[0]}")
                if page[1]:
                    content_parts.append(f"Summary: {page[1]}")
    
    context = "\n".join(content_parts) if content_parts else "No website content available."
    
    enhanced_prompt = f"""You are analyzing content from a monitored website. Use the website data below to answer the user's question accurately.

WEBSITE DATA:
{context}

IMPORTANT INSTRUCTIONS:
1. Pay attention to URLs and page titles to identify the most recent information
2. If asked about "latest" or "most recent", look for the newest pages or entries
3. Provide specific URLs when referencing pages
4. If you find relevant information, cite the specific page URL
5. If you cannot find the answer in the provided data, say so

USER QUESTION: {query}

Please provide a detailed answer based on the website data above."""
    
    try:
        answer = analyzer.chat_with_content(enhanced_prompt, api_key)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/diff', methods=['POST'])
def api_diff():
    data = request.json
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    
    import difflib
    d = difflib.HtmlDiff()
    diff_html = d.make_table(text1.splitlines(), text2.splitlines())
    
    return diff_html, 200, {'Content-Type': 'text/html'}

@app.route('/api/linkedin/login', methods=['POST'])
def api_linkedin_login():
    """Trigger interactive LinkedIn login."""
    import threading
    
    def run_login():
        linkedin_scraper.login_and_save_session()
    
    # Run in background thread to avoid blocking Flask
    thread = threading.Thread(target=run_login, daemon=True)
    thread.start()
    
    return jsonify({
        "success": True, 
        "message": "Browser opening... Please log in manually. The session will be saved automatically when you reach the feed."
    })

@app.route('/api/linkedin/scrape', methods=['POST'])
def api_linkedin_scrape():
    """Trigger LinkedIn scrape."""
    data = request.json
    url = data.get('url')
    headless = data.get('headless', True)
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    result = linkedin_scraper.scrape_linkedin_page(url, headless=headless)
    
    if "error" in result:
        return jsonify({"success": False, "message": result['error']}), 400
        
    # Save result
    storage.save_linkedin_data(url, result.get('type', 'unknown'), result)
    
    return jsonify({"success": True, "data": result})

@app.route('/api/linkedin/data', methods=['GET'])
def api_get_linkedin_data():
    """Get all saved LinkedIn data."""
    return jsonify(storage.get_linkedin_data())

if __name__ == '__main__':
    storage.init_db()
    reload_schedules()
    print("Server starting on http://localhost:5000")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
