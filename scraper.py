import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import os
from fake_useragent import UserAgent

# Initialize UserAgent
ua = UserAgent()

# Proxy Configuration (Placeholder - User should update this)
PROXIES = [
    # "http://user:pass@host:port",
]

def get_random_headers():
    """Generate random headers to avoid fingerprinting."""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def get_random_proxy():
    """Get a random proxy from the list."""
    if not PROXIES:
        return None
    return random.choice(PROXIES)

def is_valid_url(url, base_domain):
    """Check if the URL is valid and belongs to the same domain (ignoring www)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
            
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
            
        base = base_domain
        if base.startswith('www.'):
            base = base[4:]
            
        return domain == base
    except:
        return False

def fetch_page_playwright(url, use_proxy=False, save_screenshot=False):
    """Fetch page using Playwright (Headless Browser) for JS rendering."""
    from playwright.sync_api import sync_playwright
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser_args = {
                'headless': True,
            }
            
            if use_proxy:
                proxy = get_random_proxy()
                if proxy:
                    browser_args['proxy'] = {'server': proxy}
            
            browser = p.chromium.launch(**browser_args)
            
            # Create context with random user agent
            context = browser.new_context(
                user_agent=ua.random,
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            # Go to page
            page.goto(url, timeout=30000, wait_until='networkidle')
            
            # Scroll to bottom to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1) # Wait for content to load
            
            # Get content
            content = page.content()
            
            # Save screenshot if requested
            screenshot_path = None
            if save_screenshot:
                filename = f"screenshot_{int(time.time())}_{random.randint(1000,9999)}.png"
                filepath = os.path.join('static', 'screenshots', filename)
                # Ensure directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                page.screenshot(path=filepath, full_page=True)
                screenshot_path = filename # Return relative filename for URL construction
            
            browser.close()
            return content, "text/html", screenshot_path
            
    except Exception as e:
        print(f"Playwright Error fetching {url}: {e}")
        return None, None, None

def fetch_page(url, render_js=False, use_proxy=False, save_screenshot=False):
    """Fetch the HTML content of a page."""
    # If screenshots are requested, we must use Playwright (render_js=True)
    if render_js or save_screenshot:
        result = fetch_page_playwright(url, use_proxy=use_proxy, save_screenshot=save_screenshot)
        if result and result[0]:
            # Currently we only return content and type to maintain compatibility
            # Screenshot is saved to disk
            return result[0], result[1]
        return None, None
        
    try:
        headers = get_random_headers()
        proxies = None
        if use_proxy:
            proxy_url = get_random_proxy()
            if proxy_url:
                proxies = {'http': proxy_url, 'https': proxy_url}
                
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        response.raise_for_status()
        return response.text, response.headers.get('Content-Type', '')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None

def extract_text(html, content_type=''):
    """Extract readable text from HTML or XML."""
    # Determine parser based on content type
    if 'xml' in content_type.lower() or html.strip().startswith('<?xml'):
        parser = 'xml'
    else:
        parser = 'html.parser'
    
    soup = BeautifulSoup(html, parser)
    
    # Remove script and style elements
    for script in soup(['script', 'style']):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

def get_internal_links(url, html, content_type=''):
    """Extract all internal links from the page."""
    # Determine parser
    if 'xml' in content_type.lower() or html.strip().startswith('<?xml'):
        parser = 'xml'
    else:
        parser = 'html.parser'
    
    soup = BeautifulSoup(html, parser)
    base_domain = urlparse(url).netloc
    links = set()
    
    # Find all anchor tags
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Skip empty, javascript, and mailto links
        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue
        
        # Convert to absolute URL
        link = urljoin(url, href)
        
        # Check if valid and same domain
        if is_valid_url(link, base_domain):
            # Remove fragments
            parsed = urlparse(link)
            clean_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_link += f"?{parsed.query}"
            links.add(clean_link)
    
    return list(links)

# Alias for compatibility
def find_links(html, base_url):
    """Alias for get_internal_links - for API compatibility."""
    _, content_type = fetch_page(base_url)
    return get_internal_links(base_url, html, content_type or '')
