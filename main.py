import time
import argparse
import schedule
from urllib.parse import urlparse
import storage
import scraper
import analyzer
import scheduler_service

def process_url(url, visited):
    """Process a single URL: fetch, check change, summarize, save."""
    if url in visited:
        return
    visited.add(url)
    
    print(f"Checking: {url}")
    html = scraper.fetch_page(url)
    if not html:
        return

    text = scraper.extract_text(html)
    new_hash = analyzer.calculate_hash(text)
    
    # Check previous state
    old_data = storage.get_page(url)
    
    if old_data:
        if analyzer.detect_change(old_data['content_hash'], new_hash):
            print(f"  [!] CHANGE DETECTED at {url}")
            summary = analyzer.summarize_text(text)
            storage.save_page(url, new_hash, summary)
            print(f"  -> New Summary: {summary.splitlines()[0]}...")
        else:
            print(f"  [=] No change at {url}")
    else:
        print(f"  [+] New page found: {url}")
        summary = analyzer.summarize_text(text)
        storage.save_page(url, new_hash, summary)

    # Return links for crawling
    return scraper.get_internal_links(url, html)

def job(start_url):
    """The main job to run periodically."""
    print(f"\n--- Starting Job for {start_url} ---")
    storage.init_db()
    
    # BFS Queue for crawling
    queue = [start_url]
    visited = set()
    
    # Limit pages to avoid infinite loops in this demo
    MAX_PAGES = 50 
    
    while queue and len(visited) < MAX_PAGES:
        current_url = queue.pop(0)
        links = process_url(current_url, visited)
        
        if links:
            for link in links:
                if link not in visited and link not in queue:
                    queue.append(link)
                    
    print(f"--- Job Finished. Scanned {len(visited)} pages. ---")

def main():
    parser = argparse.ArgumentParser(description="Website Monitor & Scraper")
    parser.add_argument("url", help="The URL to monitor")
    parser.add_argument("--interval", type=int, default=60, help="Interval in minutes")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    # Initial run
    job(args.url)
    
    if args.once:
        return

    # Schedule
    schedule.every(args.interval).minutes.do(job, args.url)
    
    print(f"Monitoring {args.url} every {args.interval} minutes. Press Ctrl+C to stop.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
