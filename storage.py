
import sqlite3
import datetime

DB_NAME = "monitor.db"

def init_db():
    """Initialize the database with the necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check if table exists and has root_url column
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pages'")
    if cursor.fetchone():
        # Simple migration: check if root_url exists
        cursor.execute("PRAGMA table_info(pages)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'root_url' not in columns:
            print("Migrating database: Adding root_url column...")
            cursor.execute("ALTER TABLE pages ADD COLUMN root_url TEXT")
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                url TEXT PRIMARY KEY,
                content_hash TEXT,
                last_scraped TIMESTAMP,
                summary TEXT,
                root_url TEXT
            )
        ''')
    
    # Create site_summaries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_summaries (
            root_url TEXT PRIMARY KEY,
            summary TEXT,
            last_updated TIMESTAMP
        )
    ''')

    # Create schedules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            root_url TEXT PRIMARY KEY,
            interval_val INTEGER,
            interval_unit TEXT,
            is_active BOOLEAN
        )
    ''')
    
    # Create scrape_runs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_url TEXT,
            page_url TEXT,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            status TEXT,
            bytes_fetched INTEGER,
            change_detected BOOLEAN
        )
    ''')

    # Create change_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS change_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_url TEXT,
            page_url TEXT,
            detected_at TIMESTAMP,
            change_type TEXT,
            relevance_score INTEGER,
            diff_summary TEXT
        )
    ''')
    
    # Create scrape_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            content_hash TEXT,
            scraped_at TIMESTAMP,
            summary TEXT,
            changed BOOLEAN DEFAULT 0
        )
    ''')

    # Create linkedin_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS linkedin_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            type TEXT,
            data TEXT,
            scraped_at TEXT
        )
    ''')
    # Check if scrape_history has content column
    cursor.execute("PRAGMA table_info(scrape_history)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'content' not in columns:
        print("Migrating database: Adding content column to scrape_history...")
        cursor.execute("ALTER TABLE scrape_history ADD COLUMN content TEXT")

    conn.commit()
    conn.close()

# ... (rest of init_db is fine, just added migration at end of init_db or inside)
    # Actually, I should put it inside init_db before commit.

def get_page(url):
    """Retrieve a page's data by URL."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT url, content_hash, last_scraped, summary, root_url FROM pages WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "url": row[0],
            "content_hash": row[1],
            "last_scraped": row[2],
            "summary": row[3],
            "root_url": row[4]
        }
    return None

def log_scrape_run(root_url, page_url, started_at, finished_at, status, bytes_fetched, change_detected):
    """Log a scrape run execution."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scrape_runs (root_url, page_url, started_at, finished_at, status, bytes_fetched, change_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (root_url, page_url, started_at, finished_at, status, bytes_fetched, change_detected))
    conn.commit()
    conn.close()

def log_change_event(root_url, page_url, change_type="content_update", relevance_score=5, diff_summary="Content changed"):
    """Log a detected change event."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    detected_at = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO change_events (root_url, page_url, detected_at, change_type, relevance_score, diff_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (root_url, page_url, detected_at, change_type, relevance_score, diff_summary))
    conn.commit()
    conn.close()

def save_page(url, content_hash, summary, text, root_url=None):
    """Save or update a page's data and record history."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    
    # Check if content changed
    cursor.execute("SELECT content_hash FROM pages WHERE url = ?", (url,))
    row = cursor.fetchone()
    changed = False
    if row and row[0] != content_hash:
        changed = True
    
    # If root_url is not provided, try to keep existing one if updating
    if not root_url:
        cursor.execute("SELECT root_url FROM pages WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row:
            root_url = row[0]
    
    cursor.execute('''
        INSERT INTO pages (url, content_hash, last_scraped, summary, root_url)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            content_hash=excluded.content_hash,
            last_scraped=excluded.last_scraped,
            summary=excluded.summary,
            root_url=COALESCE(excluded.root_url, pages.root_url)
    ''', (url, content_hash, now, summary, root_url))
    
    # Save to history with content
    cursor.execute('''
        INSERT INTO scrape_history (url, content_hash, scraped_at, summary, changed, content)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (url, content_hash, now, summary, changed, text))
    
    conn.commit()
    conn.close()
    
    # Log change event if changed
    if changed:
        # We use a default score/summary for now, can be enhanced later
        log_change_event(root_url, url, diff_summary=summary or "Content updated")
        
    return changed

def get_scrape_history(url, limit=10):
    """Get scrape history for a URL."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT scraped_at, summary, changed 
        FROM scrape_history 
        WHERE url = ? 
        ORDER BY scraped_at DESC 
        LIMIT ?
    ''', (url, limit))
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "scraped_at": r[0],
        "summary": r[1],
        "changed": bool(r[2])
    } for r in rows]

def save_site_summary(root_url, summary):
    """Save the master summary for a root URL."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO site_summaries (root_url, summary, last_updated)
        VALUES (?, ?, ?)
        ON CONFLICT(root_url) DO UPDATE SET
            summary=excluded.summary,
            last_updated=excluded.last_updated
    ''', (root_url, summary, now))
    conn.commit()
    conn.close()

def save_schedule(root_url, interval_val, interval_unit, is_active):
    """Save or update a schedule."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedules (root_url, interval_val, interval_unit, is_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(root_url) DO UPDATE SET
            interval_val=excluded.interval_val,
            interval_unit=excluded.interval_unit,
            is_active=excluded.is_active
    ''', (root_url, interval_val, interval_unit, is_active))
    conn.commit()
    conn.close()

def get_all_schedules():
    """Get all schedules."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT root_url, interval_val, interval_unit, is_active FROM schedules")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: {"val": r[1], "unit": r[2], "active": bool(r[3])} for r in rows}

def get_pages_grouped():
    """Return all pages grouped by root_url, including master summary and schedule."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get all pages
    cursor.execute("SELECT url, last_scraped, summary, root_url FROM pages ORDER BY root_url, url")
    rows = cursor.fetchall()
    
    # Get all site summaries
    cursor.execute("SELECT root_url, summary FROM site_summaries")
    summary_rows = cursor.fetchall()
    site_summaries = {row[0]: row[1] for row in summary_rows}

    # Get all schedules
    cursor.execute("SELECT root_url, interval_val, interval_unit, is_active FROM schedules")
    sched_rows = cursor.fetchall()
    schedules = {r[0]: {"val": r[1], "unit": r[2], "active": bool(r[3])} for r in sched_rows}
    
    conn.close()
    
    grouped = {}
    for r in rows:
        url, last_scraped, summary, root_url = r
        # Fallback for old data without root_url
        group_key = root_url if root_url else "Uncategorized"
        
        if group_key not in grouped:
            grouped[group_key] = {
                "master_summary": site_summaries.get(group_key, ""),
                "schedule": schedules.get(group_key, None),
                "pages": []
            }
        
        grouped[group_key]["pages"].append({
            "url": url,
            "last_scraped": last_scraped,
            "summary": summary
        })
    return grouped

def delete_root(root_url):
    """Delete all pages, summary, and schedule associated with a root URL."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pages WHERE root_url = ?", (root_url,))
    page_count = cursor.rowcount
    cursor.execute("DELETE FROM site_summaries WHERE root_url = ?", (root_url,))
    cursor.execute("DELETE FROM schedules WHERE root_url = ?", (root_url,))
    cursor.execute("DELETE FROM scrape_runs WHERE root_url = ?", (root_url,))
    cursor.execute("DELETE FROM change_events WHERE root_url = ?", (root_url,))
    conn.commit()
    conn.close()
    return page_count

def get_analytics(time_window="24h"):
    """Generate analytics data based on the provided time window."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Calculate start time
    now = datetime.datetime.now()
    if time_window == "24h":
        start_time = now - datetime.timedelta(hours=24)
    elif time_window == "7d":
        start_time = now - datetime.timedelta(days=7)
    elif time_window == "14d":
        start_time = now - datetime.timedelta(days=14)
    else:
        start_time = now - datetime.timedelta(hours=24)
    
    start_iso = start_time.isoformat()
    
    # KPIs
    cursor.execute("SELECT COUNT(DISTINCT root_url) FROM pages")
    total_root_sites = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pages")
    total_pages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scrape_runs WHERE started_at >= ?", (start_iso,))
    scrapes_in_range = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM change_events WHERE detected_at >= ?", (start_iso,))
    changes_in_range = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scrape_runs WHERE started_at >= ? AND status = 'success'", (start_iso,))
    successful_scrapes = cursor.fetchone()[0]
    success_rate = (successful_scrapes / scrapes_in_range * 100) if scrapes_in_range > 0 else 0
    
    cursor.execute("SELECT AVG(bytes_fetched) FROM scrape_runs WHERE started_at >= ?", (start_iso,))
    avg_bytes = cursor.fetchone()[0] or 0
    
    # Avg duration
    cursor.execute("SELECT started_at, finished_at FROM scrape_runs WHERE started_at >= ? AND finished_at IS NOT NULL", (start_iso,))
    runs = cursor.fetchall()
    total_duration = 0
    count_dur = 0
    for r in runs:
        try:
            s = datetime.datetime.fromisoformat(r['started_at'])
            f = datetime.datetime.fromisoformat(r['finished_at'])
            total_duration += (f - s).total_seconds()
            count_dur += 1
        except:
            pass
    avg_duration = (total_duration / count_dur) if count_dur > 0 else 0
    
    # Trends
    cursor.execute("SELECT date(started_at) as day, COUNT(*) as count FROM scrape_runs WHERE started_at >= ? GROUP BY day", (start_iso,))
    daily_scrapes = {str(r['day']): r['count'] for r in cursor.fetchall()}
    
    cursor.execute("SELECT date(detected_at) as day, COUNT(*) as count FROM change_events WHERE detected_at >= ? GROUP BY day", (start_iso,))
    daily_changes = {str(r['day']): r['count'] for r in cursor.fetchall()}
    
    # Top Sites by Changes
    cursor.execute("SELECT root_url, COUNT(*) as count FROM change_events WHERE detected_at >= ? GROUP BY root_url ORDER BY count DESC LIMIT 5", (start_iso,))
    top_sites = [{"root_url": r['root_url'], "changes": r['count']} for r in cursor.fetchall()]
    
    # Top Pages by Changes
    cursor.execute("SELECT page_url, COUNT(*) as count FROM change_events WHERE detected_at >= ? GROUP BY page_url ORDER BY count DESC LIMIT 5", (start_iso,))
    top_pages = [{"page_url": r['page_url'], "changes": r['count']} for r in cursor.fetchall()]
    
    # Recent Activity Feed (Only changes)
    cursor.execute("SELECT url as page_url, scraped_at as date, summary, changed FROM scrape_history WHERE scraped_at >= ? AND changed=1 ORDER BY scraped_at DESC LIMIT 20", (start_iso,))
    recent_changes = [{"page_url": r['page_url'], "date": r['date'], "summary": r['summary'], "changed": bool(r['changed'])} for r in cursor.fetchall()]
    
    # Per Root Site Insights
    cursor.execute("SELECT DISTINCT root_url FROM pages")
    roots = [r[0] for r in cursor.fetchall()]
    root_insights = {}
    
    for root in roots:
        root_key = root if root else "Uncategorized"
        
        cursor.execute("SELECT COUNT(*) FROM pages WHERE root_url = ?", (root,))
        p_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(last_scraped) FROM pages WHERE root_url = ?", (root,))
        last_scraped = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scrape_runs WHERE root_url = ? AND started_at >= ?", (root, start_iso))
        s_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM change_events WHERE root_url = ? AND detected_at >= ?", (root, start_iso))
        c_count = cursor.fetchone()[0]
        
        change_rate = (c_count / s_count * 100) if s_count > 0 else 0
        
        # Most active page
        cursor.execute("SELECT page_url, COUNT(*) as cnt FROM change_events WHERE root_url = ? AND detected_at >= ? GROUP BY page_url ORDER BY cnt DESC LIMIT 1", (root, start_iso))
        active_page_row = cursor.fetchone()
        most_active_page = active_page_row['page_url'] if active_page_row else None
        
        root_insights[root_key] = {
            "total_pages": p_count,
            "last_scraped": last_scraped,
            "scrapes_in_range": s_count,
            "changes_in_range": c_count,
            "change_rate": f"{change_rate:.1f}%",
            "most_active_page": most_active_page
        }
        
    conn.close()
    
    return {
        "kpis": {
            "total_root_sites": total_root_sites,
            "total_pages": total_pages,
            "scrapes_in_range": scrapes_in_range,
            "changes_in_range": changes_in_range,
            "success_rate": f"{success_rate:.1f}%",
            "avg_scrape_duration": f"{avg_duration:.2f}s",
            "avg_bytes_fetched": f"{avg_bytes:.0f}"
        },
        "trends": {
            "daily_scrapes": daily_scrapes,
            "daily_changes": daily_changes
        },
        "top_root_sites": top_sites,
        "top_pages": top_pages,
        "recent_changes": recent_changes,
        "per_root_site_insights": root_insights
    }

def save_linkedin_data(url, type, data):
    """Save LinkedIn data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    import json
    data_json = json.dumps(data)
    
    cursor.execute('''
        INSERT INTO linkedin_data (url, type, data, scraped_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            data=excluded.data,
            scraped_at=excluded.scraped_at
    ''', (url, type, data_json, now))
    conn.commit()
    conn.close()

def get_linkedin_data():
    """Get all LinkedIn data."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM linkedin_data ORDER BY scraped_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    import json
    results = []
    for r in rows:
        try:
            d = json.loads(r['data'])
        except:
            d = {}
        results.append({
            "url": r['url'],
            "type": r['type'],
            "scraped_at": r['scraped_at'],
            "data": d
        })
    return results
