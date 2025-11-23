# Web Scraper REST API for n8n

A simple REST API that exposes web scraping functionality for easy integration with n8n, Zapier, Make.com, or any HTTP client.

## Quick Start

1. **Start the API server:**
   ```bash
   python scraper_api.py
   ```
   
   The server will start on `http://localhost:5001`

2. **Test the health endpoint:**
   ```bash
   curl http://localhost:5001/health
   ```

## Available Endpoints

### 1. GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "web-scraper-api",
  "version": "1.0.0"
}
```

### 2. GET /info
Get API information and documentation.

**Response:**
```json
{
  "service": "Web Scraper API",
  "version": "1.0.0",
  "endpoints": { ... },
  "features": [ ... ]
}
```

### 3. POST /scrape
Scrape a single URL and get content + optional AI summary.

**Request:**
```json
{
  "url": "https://example.com",
  "api_key": "sk-..." // Optional OpenAI key for AI summary
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "content_type": "html",
  "content_hash": "abc123def456...",
  "text_length": 5000,
  "text_preview": "First 500 characters...",
  "full_text": "Complete extracted text",
  "summary": "AI-generated summary (if api_key provided)"
}
```

### 4. POST /crawl
Crawl an entire website starting from a root URL.

**Request:**
```json
{
  "root_url": "https://example.com",
  "max_pages": 50,
  "api_key": "sk-..." // Optional
}
```

**Response:**
```json
{
  "success": true,
  "root_url": "https://example.com",
  "pages_crawled": 25,
  "pages": [
    {
      "url": "https://example.com/page1",
      "content_hash": "abc123",
      "text_length": 3000,
      "text_preview": "First 200 chars...",
      "summary": "AI summary if api_key provided"
    }
  ]
}
```

### 5. POST /extract-links
Extract all internal links from a URL.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "links_found": 15,
  "links": [
    "https://example.com/page1",
    "https://example.com/page2"
  ]
}
```

### 6. POST /detect-content-type
Detect content type of a URL.

**Request:**
```json
{
  "url": "https://example.com/feed.xml"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/feed.xml",
  "content_type": "xml",
  "is_html": false,
  "is_xml": true
}
```

## n8n Integration Guide

### Method 1: HTTP Request Node

1. **Add HTTP Request Node**
2. **Configure:**
   - Method: `POST`
   - URL: `http://localhost:5001/scrape`
   - Body Content Type: `JSON`
   - Body:
     ```json
     {
       "url": "{{ $json.url }}",
       "api_key": "{{ $credentials.openai.apiKey }}"
     }
     ```

### Method 2: Webhook Trigger + HTTP Request

```
Workflow:
1. Webhook (Trigger)
   └─> HTTP Request (Scrape URL)
       └─> Code (Process Results)
           └─> Database (Save Data)
```

### Example n8n Workflow

**Node 1: Webhook**
- Method: POST
- Path: scrape-url

**Node 2: HTTP Request**
- Method: POST
- URL: `http://localhost:5001/scrape`
- Body:
  ```json
  {
    "url": "{{ $json.body.url }}"
  }
  ```

**Node 3: Set (Extract Data)**
```javascript
{
  "url": "{{ $json.url }}",
  "summary": "{{ $json.summary }}",
  "hash": "{{ $json.content_hash }}"
}
```

**Node 4: Postgres/MySQL (Save)**
- Insert the extracted data into your database

## Use Cases

### 1. Monitor Website Changes
```
Schedule Trigger (Every 1 hour)
  └─> HTTP Request (/scrape)
      └─> If (content_hash changed)
          └─> Send Email/Slack Notification
```

### 2. Bulk Website Scraping
```
Google Sheets (Get URLs)
  └─> Split in Batches
      └─> HTTP Request (/scrape) [Loop]
          └─> Google Sheets (Write Results)
```

### 3. Competitive Intelligence
```
Schedule Trigger (Daily)
  └─> HTTP Request (/crawl competitor site)
      └─> Code (Analyze prices/features)
          └─> Database (Store trends)
          └─> If (price dropped)
              └─> Slack Alert
```

### 4. Content Aggregation
```
RSS Trigger (New article)
  └─> HTTP Request (/scrape article)
      └─> OpenAI (Generate summary)
          └─> WordPress (Create post)
```

## Testing with cURL

```bash
# Health check
curl http://localhost:5001/health

# Get API info
curl http://localhost:5001/info

# Scrape a URL
curl -X POST http://localhost:5001/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Scrape with AI summary
curl -X POST http://localhost:5001/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "api_key": "sk-your-openai-key"
  }'

# Crawl website
curl -X POST http://localhost:5001/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "root_url": "https://example.com",
    "max_pages": 10
  }'

# Extract links
curl -X POST http://localhost:5001/extract-links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Testing with PowerShell

```powershell
# Health check
Invoke-WebRequest -Uri http://localhost:5001/health

# Scrape URL
$body = @{
    url = "https://example.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:5001/scrape `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

## Deployment

### Local Development
```bash
python scraper_api.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 scraper_api:app
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "scraper_api:app"]
```

### Environment Variables
```bash
# Optional: Set OpenAI API key as default
export OPENAI_API_KEY=sk-your-key

# Change port
export PORT=5001
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here",
  "url": "https://example.com"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad request (missing required parameters)
- `500` - Server error (scraping failed)

## Features

✅ Simple HTTP REST API (no complex protocols)  
✅ Easy n8n integration with HTTP Request node  
✅ JSON responses  
✅ Optional AI summarization with OpenAI  
✅ HTML and XML support  
✅ Link extraction  
✅ Website crawling with depth control  
✅ Content change detection via hashing  
✅ No database required  
✅ Stateless design (perfect for automation)

## Notes

- The API runs separately from the main monitoring app (port 5001 vs 5000)
- No authentication by default (add if deploying publicly)
- OpenAI API key is optional - scraping works without it
- Default max_pages for crawling is 50
- The server uses Flask development mode - use Gunicorn for production
