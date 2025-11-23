from flask import Flask, render_template, jsonify, request
import threading
import time
import datetime
import schedule
import sqlite3
import storage
import scraper
import analyzer
from scheduler_service import SchedulerService

app = Flask(__name__)

# Global variable to store API Key (in memory for now)
# In production, use environment variables or secure storage
OPENAI_API_KEY = None

# --- Background Scheduler ---
scheduler = SchedulerService()

# --- Helpers ---
def get_all_pages_grouped():
    return storage.get_pages_grouped()

def crawl_and_scrape(start_url, api_key):
    """
    Recursively crawl and scrape pages starting from start_url.
    Run this in a background thread.
    """
    print(f"Starting crawl for {start_url}")
    queue = [start_url]
    visited = set()
    MAX_PAGES = 20 # Limit for safety

    while queue and len(visited) < MAX_PAGES:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        
        print(f"Processing: {url}")
        start_time = datetime.datetime.now().isoformat()
        html, content_type = scraper.fetch_page(url)
        
        if not html:
            # Log failed run
            storage.log_scrape_run(start_url, url, start_time, datetime.datetime.now().isoformat(), "failed", 0, False)
            continue

        text = scraper.extract_text(html, content_type)
        bytes_fetched = len(html.encode('utf-8'))
        new_hash = analyzer.calculate_hash(text)
        
        # Generate summary
        summary = analyzer.summarize_text(text, api_key)
        
        # Save with root_url (returns True if changed)
        changed = storage.save_page(url, new_hash, summary, text, root_url=start_url)
        
        # Log successful run
        storage.log_scrape_run(start_url, url, start_time, datetime.datetime.now().isoformat(), "success", bytes_fetched, changed)
        
        # Find links
        links = scraper.get_internal_links(url, html, content_type)
        for link in links:
            if link not in visited and link not in queue:
                queue.append(link)
    
    print(f"Crawl finished for {start_url}")
    
    # --- Generate Master Summary ---
    if api_key:
        print(f"Generating master summary for {start_url}...")
        # Fetch all pages for this root to get their summaries
        # (We could optimize this by collecting them during crawl, but DB is safer)
        grouped = storage.get_pages_grouped()
        # Note: get_pages_grouped returns a dict structure now
        root_data = grouped.get(start_url)
        
        if root_data:
            summaries = [p['summary'] for p in root_data['pages'] if p['summary']]
            master_summary = analyzer.generate_master_summary(summaries, api_key)
            storage.save_site_summary(start_url, master_summary)
            print(f"Master summary saved for {start_url}")

def perform_scrape_job(url):
    """Wrapper to run crawl in background."""
    # We need to ensure the API key is available to the job
    # In a real app, we might store the key in the DB or env
    thread = threading.Thread(target=crawl_and_scrape, args=(url, OPENAI_API_KEY))
    thread.start()

def reload_schedules():
    """Reload all active schedules from DB."""
    schedules = storage.get_all_schedules()
    for root_url, data in schedules.items():
        if data['active']:
            scheduler.add_job(root_url, data['val'], data['unit'], perform_scrape_job, root_url)
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
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    # Update global key if provided
    global OPENAI_API_KEY
    if api_key:
        OPENAI_API_KEY = api_key
    
    # Start background crawl immediately
    perform_scrape_job(url)
    
    # Save schedule and add job
    storage.save_schedule(url, interval_val, interval_unit, True)
    scheduler.add_job(url, interval_val, interval_unit, perform_scrape_job, url)
    
    return jsonify({"success": True, "message": "Started crawling and monitoring..."})

@app.route('/api/schedule/toggle', methods=['POST'])
def api_toggle_schedule():
    data = request.json
    root_url = data.get('root_url')
    is_active = data.get('is_active')
    
    if not root_url:
        return jsonify({"error": "Root URL is required"}), 400
        
    # Get existing schedule to know interval
    schedules = storage.get_all_schedules()
    if root_url not in schedules:
        return jsonify({"error": "Schedule not found"}), 404
        
    current = schedules[root_url]
    
    # Update DB
    storage.save_schedule(root_url, current['val'], current['unit'], is_active)
    
    # Update Scheduler
    if is_active:
        scheduler.add_job(root_url, current['val'], current['unit'], perform_scrape_job, root_url)
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
    scheduler.remove_job(root_url) # Stop monitoring
    return jsonify({"success": True, "message": f"Deleted {count} pages."})

@app.route('/api/scrape', methods=['POST'])
def api_trigger_scrape():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    perform_scrape_job(url)
    return jsonify({"success": True, "message": "Scrape triggered in background"})

@app.route('/api/history/<path:url>', methods=['GET'])
def api_get_history(url):
    """Get scrape history for a specific URL."""
    history = storage.get_scrape_history(url, limit=20)
    return jsonify(history)

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
    
    # Build intelligent context from database
    content_parts = []
    
    if url:
        import sqlite3
        conn = sqlite3.connect('monitor.db')
        cursor = conn.cursor()
        
        # Check if this is a root URL with multiple pages
        cursor.execute('SELECT COUNT(*) FROM pages WHERE root_url = ?', (url,))
        page_count = cursor.fetchone()[0]
        
        if page_count > 0:
            # Get ALL pages for this root URL from database with their latest content
            cursor.execute('''
                SELECT p.url, p.summary, p.last_scraped, h.content
                FROM pages p
                LEFT JOIN (
                    SELECT url, content, scraped_at
                    FROM scrape_history
                    WHERE (url, scraped_at) IN (
                        SELECT url, MAX(scraped_at) 
                        FROM scrape_history 
                        GROUP BY url
                    )
                ) h ON p.url = h.url
                WHERE p.root_url = ?
                ORDER BY p.last_scraped DESC
                LIMIT 50
            ''', (url,))
            
            pages = cursor.fetchall()
            
            if pages:
                content_parts.append(f"Website: {url}")
                content_parts.append(f"Total pages monitored: {len(pages)}\n")
                
                for idx, (page_url, summary, last_scraped, full_content) in enumerate(pages, 1):
                    content_parts.append(f"\n=== PAGE {idx}: {page_url} ===")
                    content_parts.append(f"Last scraped: {last_scraped}")
                    if summary:
                        content_parts.append(f"Summary: {summary}")
                    if full_content:
                        # Limit content per page to avoid token limits
                        content_parts.append(f"Content:\n{full_content[:3000]}")
                    content_parts.append("")
            
            conn.close()
        
        # Fallback: If no pages in DB, scrape the URL fresh
        if not content_parts:
            html, content_type = scraper.fetch_page(url, render_js=True)
            if html:
                text = scraper.extract_text(html, content_type)
                content_parts.append(f"Page: {url}\n{text}")
    
    if not content_parts:
        return jsonify({"error": "Could not fetch content from URL"}), 400
    
    # Join all content
    full_context = "\n".join(content_parts)
    
    # Enhanced prompt to help LLM understand structure
    enhanced_query = f"""Based on the following website content with multiple pages, please answer this question: {query}

Important: 
- Each page section starts with "=== PAGE X: [URL] ==="
- Pay attention to page URLs to provide specific links
- Look across ALL pages to find the most recent information
- If asked for URLs, provide the actual page URLs shown in the content

Question: {query}"""
    
    answer = analyzer.chat_with_content(full_context, enhanced_query, api_key)
    return jsonify({"answer": answer})

@app.route('/api/diff', methods=['POST'])
def api_diff():
    data = request.json
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    import difflib
    d = difflib.HtmlDiff()
    return d.make_file(text1.splitlines(), text2.splitlines(), context=True, numlines=2)

@app.route('/api/recent-changes', methods=['GET'])
def api_recent_changes():
    """Get recent change events."""
    import sqlite3
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 10, type=int)
    
    cursor.execute('''
        SELECT page_url, detected_at, diff_summary, root_url
        FROM change_events
        ORDER BY detected_at DESC
        LIMIT ?
    ''', (limit,))
    
    changes = []
    for row in cursor.fetchall():
        changes.append({
            'url': row[0],
            'detected_at': row[1],
            'summary': row[2],
            'root_url': row[3]
        })
    
    conn.close()
    return jsonify(changes)

if __name__ == '__main__':
    app.config['JSON_SORT_KEYS'] = False
    app.json.sort_keys = False
    storage.init_db()
    reload_schedules() # Restore schedules on startup
    app.run(debug=True, port=5000, use_reloader=False)
