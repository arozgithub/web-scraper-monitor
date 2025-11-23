# Implementation Plan - Website Monitor & Scraper

The goal is to build a Python-based tool that scrapes a website, detects changes, and generates summaries on a schedule.

## User Review Required
> [!IMPORTANT]
> **Summarization Method**: I have assumed we will use a placeholder or a basic NLP library for summarization. If you have an API key (e.g., OpenAI, Gemini) you'd like to use, please let me know.
> **Target Website**: The tool will be designed to accept a URL as input.

## Proposed Changes

### Project Structure
We will create a modular Python project:
- `main.py`: Entry point.
- `scraper.py`: Handles fetching and parsing HTML.
- `storage.py`: Handles SQLite database interactions.
- `analyzer.py`: Handles change detection and summarization.
- `scheduler_service.py`: Handles the scheduling logic.

### Dependencies
- `requests`: For HTTP requests.
- `beautifulsoup4`: For HTML parsing.
- `schedule`: For task scheduling.
- `sqlite3`: (Standard lib) For data persistence.

### [NEW] `storage.py`
- `init_db()`: Create tables `pages` (url, content_hash, last_scraped, summary).
- `get_page(url)`: Retrieve last state.
- `save_page(url, content, hash, summary)`: Update state.

### [NEW] `scraper.py`
- `crawl(start_url)`: Recursive function to find internal links and scrape content.
- `extract_text(html)`: Clean HTML to get readable text.

### [NEW] `analyzer.py`
- `calculate_hash(text)`: SHA256 hash of content.
- `detect_change(old_hash, new_hash)`: Boolean check.
- `summarize(text)`: Function to generate summary (Placeholder/Simple implementation initially).

### [NEW] `scheduler_service.py`
- `start_schedule(interval, job_function)`: Runs the job periodically.

### [NEW] `main.py`
- CLI to start the monitor, set target URL, and interval.

## Web Interface (New)
We will add a Flask web server to provide a GUI.

### Dependencies
- `flask`: For the web server.

### [NEW] `app.py`
- Flask application serving the frontend and API.
- `GET /api/pages`: Returns list of monitored pages.
- `POST /api/pages`: Adds a new URL to monitor.
- `POST /api/scrape`: Triggers a scrape for a specific URL.
- Background thread for the scheduler (integrated from `scheduler_service`).

### [NEW] `templates/index.html`
- Single Page Application (SPA) structure.
- Sections: Dashboard (Stats), URL List, Add URL Form.

### [NEW] `static/style.css`
- Premium design: Dark mode, gradients, glassmorphism cards.
- Responsive layout.

### [NEW] `static/script.js`
- Fetch API to communicate with backend.
- Dynamic DOM updates.

## UI Refinement & Data Restructuring (New)
We will restructure the data to group pages by their "Root URL" (the URL the user entered).

### Database Changes (`storage.py`)
- Add `root_url` column to `pages` table.
- `get_pages_grouped()`: Return pages grouped by `root_url`.
- `delete_root(root_url)`: Delete all pages associated with a root URL.

### API Changes (`app.py`)
- `GET /api/pages`: Returns data grouped by root URL.
- `DELETE /api/pages`: Deletes a root URL and its children.

### Frontend Changes
- **Card Design**: Each card represents a Root URL.
- **Expandable**: Clicking a card reveals a list/table of scraped child pages with their summaries.
- **Delete Button**: Remove the entire group.

## Global Site Summarization (New)
We will generate a single "Master Summary" for the entire scraped site.

### Database Changes (`storage.py`)
- New table `site_summaries` (root_url, summary, last_updated).
- `save_site_summary(root_url, summary)`
- `get_site_summary(root_url)`

### Analyzer Changes (`analyzer.py`)
- `generate_master_summary(page_summaries, api_key)`: Aggregates individual summaries into one.

### Backend Changes (`app.py`)
- In `crawl_and_scrape`, after the loop finishes:
    1. Fetch all summaries for the `root_url`.
    2. Call `generate_master_summary`.
    3. Save to DB.
- Update `get_all_pages_grouped` to include the master summary in the response.

### Frontend Changes
- Display the "Master Summary" prominently in the expanded root card header.

## Advanced Scheduling & Automation (New)
Allow users to configure scrape intervals and toggle monitoring on/off.

### Database Changes (`storage.py`)
- New table `schedules` (root_url, interval_val, interval_unit, is_active).
- `save_schedule(root_url, val, unit, active)`
- `get_schedule(root_url)`
- `get_all_active_schedules()`

### Scheduler Changes (`scheduler_service.py`)
- Refactor into a `SchedulerService` class.
- Use `schedule` library with tags (tag=root_url) to manage individual jobs.
- `add_job(root_url, val, unit)`
# Implementation Plan - Website Monitor & Scraper

The goal is to build a Python-based tool that scrapes a website, detects changes, and generates summaries on a schedule.

## User Review Required
> [!IMPORTANT]
> **Summarization Method**: I have assumed we will use a placeholder or a basic NLP library for summarization. If you have an API key (e.g., OpenAI, Gemini) you'd like to use, please let me know.
> **Target Website**: The tool will be designed to accept a URL as input.

## Proposed Changes

### Project Structure
We will create a modular Python project:
- `main.py`: Entry point.
- `scraper.py`: Handles fetching and parsing HTML.
- `storage.py`: Handles SQLite database interactions.
- `analyzer.py`: Handles change detection and summarization.
- `scheduler_service.py`: Handles the scheduling logic.

### Dependencies
- `requests`: For HTTP requests.
- `beautifulsoup4`: For HTML parsing.
- `schedule`: For task scheduling.
- `sqlite3`: (Standard lib) For data persistence.

### [NEW] `storage.py`
- `init_db()`: Create tables `pages` (url, content_hash, last_scraped, summary).
- `get_page(url)`: Retrieve last state.
- `save_page(url, content, hash, summary)`: Update state.

### [NEW] `scraper.py`
- `crawl(start_url)`: Recursive function to find internal links and scrape content.
- `extract_text(html)`: Clean HTML to get readable text.

### [NEW] `analyzer.py`
- `calculate_hash(text)`: SHA256 hash of content.
- `detect_change(old_hash, new_hash)`: Boolean check.
- `summarize(text)`: Function to generate summary (Placeholder/Simple implementation initially).

### [NEW] `scheduler_service.py`
- `start_schedule(interval, job_function)`: Runs the job periodically.

### [NEW] `main.py`
- CLI to start the monitor, set target URL, and interval.

## Web Interface (New)
We will add a Flask web server to provide a GUI.

### Dependencies
- `flask`: For the web server.

### [NEW] `app.py`
- Flask application serving the frontend and API.
- `GET /api/pages`: Returns list of monitored pages.
- `POST /api/pages`: Adds a new URL to monitor.
- `POST /api/scrape`: Triggers a scrape for a specific URL.
- Background thread for the scheduler (integrated from `scheduler_service`).

### [NEW] `templates/index.html`
- Single Page Application (SPA) structure.
- Sections: Dashboard (Stats), URL List, Add URL Form.

### [NEW] `static/style.css`
- Premium design: Dark mode, gradients, glassmorphism cards.
- Responsive layout.

### [NEW] `static/script.js`
- Fetch API to communicate with backend.
- Dynamic DOM updates.

## UI Refinement & Data Restructuring (New)
We will restructure the data to group pages by their "Root URL" (the URL the user entered).

### Database Changes (`storage.py`)
- Add `root_url` column to `pages` table.
- `get_pages_grouped()`: Return pages grouped by `root_url`.
- `delete_root(root_url)`: Delete all pages associated with a root URL.

### API Changes (`app.py`)
- `GET /api/pages`: Returns data grouped by root URL.
- `DELETE /api/pages`: Deletes a root URL and its children.

### Frontend Changes
- **Card Design**: Each card represents a Root URL.
- **Expandable**: Clicking a card reveals a list/table of scraped child pages with their summaries.
- **Delete Button**: Remove the entire group.

## Global Site Summarization (New)
We will generate a single "Master Summary" for the entire scraped site.

### Database Changes (`storage.py`)
- New table `site_summaries` (root_url, summary, last_updated).
- `save_site_summary(root_url, summary)`
- `get_site_summary(root_url)`

### Analyzer Changes (`analyzer.py`)
- `generate_master_summary(page_summaries, api_key)`: Aggregates individual summaries into one.

### Backend Changes (`app.py`)
- In `crawl_and_scrape`, after the loop finishes:
    1. Fetch all summaries for the `root_url`.
    2. Call `generate_master_summary`.
    3. Save to DB.
- Update `get_all_pages_grouped` to include the master summary in the response.

### Frontend Changes
- Display the "Master Summary" prominently in the expanded root card header.

## Advanced Scheduling & Automation (New)
Allow users to configure scrape intervals and toggle monitoring on/off.

### Database Changes (`storage.py`)
- New table `schedules` (root_url, interval_val, interval_unit, is_active).
- `save_schedule(root_url, val, unit, active)`
- `get_schedule(root_url)`
- `get_all_active_schedules()`

### Scheduler Changes (`scheduler_service.py`)
- Refactor into a `SchedulerService` class.
- Use `schedule` library with tags (tag=root_url) to manage individual jobs.
- `add_job(root_url, val, unit)`
- `remove_job(root_url)`
- `reload_jobs()`: Load from DB on startup.

## Proposed Changes

### Frontend (`templates/index.html`)
- Add Chart.js CDN.
- Add Navigation Tabs (Monitor vs Analytics).
- Add Analytics Container (hidden by default).
    - Time window selector (24h, 7d, 14d).
    - KPIs Grid.
    - Charts Section (Scrapes vs Changes).
    - Top Lists (Sites/Pages).
    - Recent Changes Feed.

### Frontend Logic (`static/script.js`)
- Add `showTab(tabName)` function.
- Add `loadAnalytics(window)` function.
- Add `renderCharts(data)` using Chart.js.
- Add `renderKPIs(data)` and other render helpers.

### Styling (`static/style.css`)
- Add styles for Tabs.
- Add styles for Analytics Grid and Charts.
- Add styles for KPI cards (glassmorphism).

### Backend Changes (`app.py`)
- Initialize `SchedulerService`.
- `POST /api/pages`: Accept schedule params, save to DB, add job.
- `POST /api/schedule/toggle`: Update DB, add/remove job.
- `GET /api/pages`: Include schedule info in response.

## Verification Plan
### Automated Tests
- Unit tests for hash calculation and change detection logic.
- Mocked tests for scraper to avoid hitting real sites during testing.

### Manual Verification
- Click "Analytics" tab.
- Verify data loads (KPIs, Charts).
- Switch time windows.
- Verify Charts render correctly.
- Run against a test page (e.g., a local HTML file or a controlled public site).
- Modify the test page and verify the tool reports "Changed".
- Check the generated summary.
