# 🚀 Enterprise Web Scraper & Monitor

A powerful, enterprise-grade web scraping and monitoring system with AI-powered features, built for automated change detection, RAG chat, and n8n integration.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

### Core Scraping
- 🌐 **Multi-page crawling** with intelligent link extraction
- 📊 **Change detection** using content hashing
- ⏰ **Scheduled monitoring** with customizable intervals
- 🎯 **Smart filtering** (same-domain validation, www handling)

### Enterprise Features
- 🤖 **Headless Browser (Playwright)** - Render JavaScript SPAs
- 🔄 **Smart Proxy Rotation** - Avoid IP bans
- 🎭 **Anti-Fingerprinting** - Random User-Agents
- 💬 **RAG Chat** - Ask questions about website content using AI
- 📸 **Screenshot Monitoring** - Visual change tracking
- 🔍 **Visual Diffing** - Side-by-side content comparison

### Integrations
- 🔌 **n8n Ready** - Full API for workflow automation
- 🌍 **ngrok Support** - Secure public tunnels
- 📈 **Analytics Dashboard** - Visual insights & trends

## 🏗️ Architecture

```
┌─────────────────┐
│   Web UI        │  (Flask - Port 5000)
│   localhost     │
└────────┬────────┘
         │
         ├─────> Scheduler (Background Jobs)
         │
         ├─────> Storage (SQLite)
         │
         └─────> Scraper Module
                     │
                     ├─> Playwright (JS Rendering)
                     ├─> BeautifulSoup (HTML Parsing)
                     └─> Analyzer (OpenAI Integration)

┌─────────────────┐
│   API Server    │  (Flask - Port 5001)
│   n8n Gateway   │
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API Key (for AI features)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/enterprise-scraper.git
cd enterprise-scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Configuration

1. **Proxy Setup** (Optional)
   Edit `scraper.py` and add your proxy URLs:
   ```python
   PROXIES = [
       "http://user:pass@proxy1:port",
       "http://user:pass@proxy2:port",
   ]
   ```

2. **OpenAI API Key**
   - Set via UI when using AI features
   - Or set environment variable: `OPENAI_API_KEY`

### Running

```bash
# Start both UI and API servers
.\run.bat  # Windows
# Or manually:
python app.py          # Terminal 1 (UI)
python scraper_api.py  # Terminal 2 (API)
```

Access the application:
- **Web UI**: http://localhost:5000
- **API**: http://localhost:5001

## 📖 Usage Guide

### 1. Monitor a Website

1. Open http://localhost:5000
2. Click "Monitor" tab
3. Enter website URL
4. Set OpenAI API key
5. Choose monitoring interval
6. Click "Start Monitoring"

### 2. Chat with Website (RAG)

1. Go to "Chat (RAG)" tab
2. Enter the root URL of a monitored site
3. Provide OpenAI API key
4. Ask questions like:
   - "What is the most recent release?"
   - "Give me the URL for version 25.11"
   - "What changed in the latest update?"

### 3. n8n Integration

See [N8N_INTEGRATION_GUIDE.md](N8N_INTEGRATION_GUIDE.md) for complete workflow examples.

**Example API Call:**
```bash
curl -X POST http://localhost:5001/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "render_js": true,
    "use_proxy": false
  }'
```

## 🔧 API Endpoints

### Scraping
- `POST /scrape` - Scrape single page
- `POST /scrape-complete` - Full site crawl
- `POST /screenshot` - Take screenshot

### Analysis
- `POST /chat` - RAG chat with content
- `POST /diff` - Visual diff of two texts

### Utility
- `GET /health` - Health check
- `GET /info` - API information

Full API documentation: [ENTERPRISE_FEATURES.md](ENTERPRISE_FEATURES.md)

## 📊 Database Schema

**Tables:**
- `pages` - Monitored pages and metadata
- `scrape_history` - Full scraping history with content
- `change_events` - Detected changes log
- `scrape_runs` - Performance metrics
- `schedules` - Monitoring schedules
- `site_summaries` - AI-generated summaries

## 🛠️ Advanced Configuration

### Headless Browser Options
```python
# In scraper.py - fetch_page_playwright()
browser_args = {
    'headless': True,  # Run in background
    'args': ['--no-sandbox']  # Additional Chrome flags
}
```

### Scraping Limits
```python
# In app.py - crawl_and_scrape()
MAX_PAGES = 20  # Max pages per crawl
```

## 📁 Project Structure

```
enterprise-scraper/
├── app.py                      # Main UI server
├── scraper_api.py              # API server
├── scraper.py                  # Core scraping logic
├── analyzer.py                 # AI analysis
├── storage.py                  # Database operations
├── scheduler.py                # Job scheduling
├── templates/
│   └── index.html              # Web UI
├── static/
│   ├── style.css
│   ├── script.js
│   └── screenshots/            # Saved screenshots
├── requirements.txt
├── run.bat                     # Startup script
└── ENTERPRISE_FEATURES.md      # Feature documentation
```

## 🐛 Troubleshooting

### "Changes not detected"
- Websites must actually change for detection
- Check Analytics tab for change history
- See [CHANGE_DETECTION_STATUS.md](CHANGE_DETECTION_STATUS.md)

### "RAG Chat not working"
- Ensure server restarted after updates
- Check database has content (not just hashes)
- Use exact root URL from Monitor tab
- See [RAG_IMPROVEMENTS.md](RAG_IMPROVEMENTS.md)

### Port Already in Use
```bash
# Windows: Find and kill process
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Playwright** - Headless browser automation
- **BeautifulSoup** - HTML parsing
- **OpenAI** - AI-powered features
- **Flask** - Web framework

## 🔗 Resources

- [Documentation](ENTERPRISE_FEATURES.md)
- [n8n Integration Guide](N8N_INTEGRATION_GUIDE.md)
- [Change Detection Guide](CHANGE_DETECTION_STATUS.md)
- [RAG Improvements](RAG_IMPROVEMENTS.md)

---

**Built with ❤️ for enterprise web monitoring**
