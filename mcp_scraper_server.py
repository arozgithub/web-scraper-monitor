"""
MCP Server for Web Scraping
Exposes scraping functionality via Model Context Protocol for use with n8n and other integrations.
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, ResourceTemplate
import scraper
import analyzer

# Initialize MCP server
app = Server("web-scraper")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available scraping tools."""
    return [
        Tool(
            name="scrape_url",
            description="Scrape a single URL and return its content and summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to scrape"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "OpenAI API key for summarization (optional)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="crawl_website",
            description="Crawl a website starting from a root URL, following internal links",
            inputSchema={
                "type": "object",
                "properties": {
                    "root_url": {
                        "type": "string",
                        "description": "The root URL to start crawling from"
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to crawl (default: 50)",
                        "default": 50
                    },
                    "api_key": {
                        "type": "string",
                        "description": "OpenAI API key for summarization (optional)"
                    }
                },
                "required": ["root_url"]
            }
        ),
        Tool(
            name="extract_links",
            description="Extract all internal links from a given URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract links from"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="detect_content_type",
            description="Detect whether a URL serves HTML or XML content",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to check"
                    }
                },
                "required": ["url"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "scrape_url":
        url = arguments["url"]
        api_key = arguments.get("api_key")
        
        try:
            # Fetch the page
            html, content_type = scraper.fetch_page(url)
            if not html:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Failed to fetch URL", "url": url})
                )]
            
            # Extract text
            text = scraper.extract_text(html, content_type)
            content_hash = analyzer.calculate_hash(text)
            
            # Generate summary if API key provided
            summary = None
            if api_key:
                summary = analyzer.summarize(text, api_key)
            
            result = {
                "url": url,
                "content_type": content_type,
                "content_hash": content_hash,
                "text_length": len(text),
                "text_preview": text[:500] + "..." if len(text) > 500 else text,
                "summary": summary
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e), "url": url})
            )]
    
    elif name == "crawl_website":
        root_url = arguments["root_url"]
        max_pages = arguments.get("max_pages", 50)
        api_key = arguments.get("api_key")
        
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
                    "summary": summary
                })
                
                # Find new links to visit
                if content_type == "html":
                    internal_links = scraper.find_links(html, current_url)
                    for link in internal_links:
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)
            
            result = {
                "root_url": root_url,
                "pages_crawled": len(pages_data),
                "pages": pages_data
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e), "root_url": root_url})
            )]
    
    elif name == "extract_links":
        url = arguments["url"]
        
        try:
            html, content_type = scraper.fetch_page(url)
            if not html or content_type != "html":
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Not an HTML page or failed to fetch", "url": url})
                )]
            
            links = scraper.find_links(html, url)
            
            result = {
                "url": url,
                "links_found": len(links),
                "links": links
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e), "url": url})
            )]
    
    elif name == "detect_content_type":
        url = arguments["url"]
        
        try:
            html, content_type = scraper.fetch_page(url)
            
            result = {
                "url": url,
                "content_type": content_type,
                "is_html": content_type == "html",
                "is_xml": content_type == "xml"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e), "url": url})
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="scraper://capabilities",
            name="Scraper Capabilities",
            mimeType="application/json",
            description="Information about scraper capabilities and supported features"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
    if uri == "scraper://capabilities":
        capabilities = {
            "features": [
                "HTML scraping with BeautifulSoup",
                "XML parsing support",
                "Automatic content type detection",
                "Internal link extraction",
                "Website crawling with depth control",
                "Content hashing for change detection",
                "AI-powered summarization (with OpenAI API key)"
            ],
            "supported_content_types": ["text/html", "application/xhtml+xml", "application/xml", "text/xml"],
            "max_pages_per_crawl": 50,
            "libraries": {
                "requests": "HTTP client",
                "beautifulsoup4": "HTML/XML parsing",
                "lxml": "Fast XML/HTML parser",
                "openai": "AI summarization"
            }
        }
        return json.dumps(capabilities, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
