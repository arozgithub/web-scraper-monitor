# MCP Web Scraper Server

A standalone Model Context Protocol (MCP) server that exposes web scraping functionality for use with n8n, Claude Desktop, and other MCP-compatible tools.

## Features

- **scrape_url**: Scrape a single URL and get content + AI summary
- **crawl_website**: Crawl entire websites following internal links
- **extract_links**: Extract all internal links from a page
- **detect_content_type**: Detect HTML vs XML content

## Installation

1. Install MCP SDK:
```bash
pip install mcp
```

2. The server uses existing scraper modules, so no additional dependencies needed.

## Usage

### With Claude Desktop

Add to your Claude Desktop config (`%APPDATA%\Claude\config.json` on Windows):

```json
{
  "mcpServers": {
    "web-scraper": {
      "command": "python",
      "args": ["c:/Scraper/mcp_scraper_server.py"]
    }
  }
}
```

### With n8n

1. Install the MCP node in n8n (if available) or use HTTP Request node
2. Run the server: `python mcp_scraper_server.py`
3. Configure n8n to communicate via stdio or HTTP

### Standalone Testing

Run the server directly:
```bash
python mcp_scraper_server.py
```

## Available Tools

### 1. scrape_url
Scrape a single URL and return structured data.

**Input:**
```json
{
  "url": "https://example.com",
  "api_key": "sk-..." // Optional OpenAI key for summarization
}
```

**Output:**
```json
{
  "url": "https://example.com",
  "content_type": "html",
  "content_hash": "abc123...",
  "text_length": 5000,
  "text_preview": "...",
  "summary": "AI-generated summary"
}
```

### 2. crawl_website
Crawl an entire website starting from a root URL.

**Input:**
```json
{
  "root_url": "https://example.com",
  "max_pages": 50,
  "api_key": "sk-..." // Optional
}
```

**Output:**
```json
{
  "root_url": "https://example.com",
  "pages_crawled": 25,
  "pages": [
    {
      "url": "https://example.com/page1",
      "content_hash": "abc123",
      "text_length": 3000,
      "summary": "..."
    }
  ]
}
```

### 3. extract_links
Extract all internal links from a URL.

**Input:**
```json
{
  "url": "https://example.com"
}
```

**Output:**
```json
{
  "url": "https://example.com",
  "links_found": 15,
  "links": ["https://example.com/page1", ...]
}
```

### 4. detect_content_type
Detect content type of a URL.

**Input:**
```json
{
  "url": "https://example.com/feed.xml"
}
```

**Output:**
```json
{
  "url": "https://example.com/feed.xml",
  "content_type": "xml",
  "is_html": false,
  "is_xml": true
}
```

## Available Resources

### scraper://capabilities
Returns information about scraper features and supported content types.

## Integration Examples

### n8n Workflow Example

```
1. HTTP Request Node (trigger)
2. MCP Tool Call Node
   - Tool: scrape_url
   - URL: {{$json.url}}
3. Code Node (process results)
4. Database Node (save data)
```

### Python Script Example

```python
from mcp import ClientSession
import asyncio

async def scrape_example():
    async with ClientSession() as session:
        result = await session.call_tool(
            "scrape_url",
            {"url": "https://example.com"}
        )
        print(result)

asyncio.run(scrape_example())
```

## Notes

- The server runs in stdio mode by default (suitable for Claude Desktop)
- For HTTP mode (n8n), you may need to wrap it with an HTTP adapter
- OpenAI API key is optional; without it, no AI summaries are generated
- Default max pages for crawling is 50 to prevent excessive resource usage
