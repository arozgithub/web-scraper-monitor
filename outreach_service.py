import re
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import storage
import scraper
import analyzer

# Google Custom Search API Configuration
GOOGLE_API_KEY = "AIzaSyAQ2ztxkSiEvLqrxRgnwmdy_5PdycFIIk0"
GOOGLE_CSE_ID = "8215253ebc71b44bc"  # Custom Search Engine ID

def search_leads_google_api(keywords, location, max_results=50):
    """
    Search using Google Custom Search API (official, reliable).
    Requires API key and Custom Search Engine ID.
    """
    import requests
    from urllib.parse import urlparse
    
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_API_KEY":
        print("Google API key not configured")
        return []
    
    if not GOOGLE_CSE_ID or GOOGLE_CSE_ID == "YOUR_SEARCH_ENGINE_ID":
        print("Google Custom Search Engine ID not configured")
        print("Create one at: https://programmablesearchengine.google.com/")
        return []
    
    query = f"{keywords} {location}"
    leads = []
    
    try:
        # Google Custom Search API endpoint
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Calculate how many pages we need (10 results per page max)
        num_pages = min((max_results // 10) + 1, 10)  # Max 10 pages (100 results)
        
        for page in range(num_pages):
            start_index = (page * 10) + 1
            
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': query,
                'start': start_index,
                'num': min(10, max_results - len(leads))
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        result_url = item.get('link', '')
                        
                        # Skip unwanted domains
                        if any(x in result_url.lower() for x in ['google.com', 'youtube.com', 'facebook.com']):
                            continue
                        
                        try:
                            parsed = urlparse(result_url)
                            domain = parsed.netloc.replace('www.', '')
                            
                            if domain and result_url not in [l['url'] for l in leads]:
                                leads.append({
                                    'company_name': domain,
                                    'url': result_url,
                                    'location': location
                                })
                                
                                if len(leads) >= max_results:
                                    break
                        except:
                            continue
                else:
                    print("No more results from Google API")
                    break
            elif response.status_code == 429:
                print("Google API rate limit reached")
                break
            else:
                print(f"Google API error: {response.status_code}")
                if response.status_code == 400:
                    print("Response:", response.text)
                break
            
            if len(leads) >= max_results:
                break
        
        print(f"Google Custom Search API found {len(leads)} URLs")
        
    except Exception as e:
        print(f"Google API error: {e}")
    
    return leads

def search_leads_yelp(keywords, location, max_results=50):
    """
    Search for companies on Yelp (simplified version).
    In a real implementation, you would use Yelp API or scrape search results.
    For now, this is a placeholder that returns sample companies.
    """
    # TODO: Implement actual Yelp search
    # This is a placeholder - in production, use Yelp API or web scraping
    return []

def search_leads_duckduckgo(keywords, location, max_results=50):
    """
    Search using DuckDuckGo (less restrictive than Google).
    """
    from bs4 import BeautifulSoup
    import requests
    
    query = f"{keywords} {location}"
    search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    leads = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # DuckDuckGo results are in <a> tags with class 'result__url'
            result_links = soup.find_all('a', class_='result__url')
            
            seen = set()
            for link in result_links:
                # Get the href or the text content
                url = link.get('href', '')
                if not url:
                    # Sometimes the URL is in the text
                    url = link.get_text(strip=True)
                
                # Clean and validate URL
                if not url.startswith('http'):
                    url = 'https://' + url
                
                # Skip unwanted domains
                if any(x in url.lower() for x in ['google.com', 'facebook.com', 'youtube.com', 'yelp.com']):
                    continue
                
                if url not in seen and len(seen) < max_results:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc.replace('www.', '')
                        
                        if domain:
                            seen.add(url)
                            leads.append({
                                'company_name': domain,
                                'url': url,
                                'location': location
                            })
                    except:
                        continue
            
            print(f"DuckDuckGo found {len(leads)} URLs")
            
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
    
    return leads

def search_leads_google_playwright(keywords, location, max_results=50):
    """
    Search Google using Playwright (JavaScript rendering).
    This bypasses some bot detection.
    """
    leads = []
    
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        
        query = f"{keywords} {location}"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=50"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            page.goto(search_url, timeout=15000)
            page.wait_for_timeout(2000)  # Wait for content to load
            
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for result links
            seen = set()
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                if '/url?q=' in href:
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    
                    if actual_url.startswith('http') and 'google.com' not in actual_url:
                        try:
                            from urllib.parse import urlparse, unquote
                            actual_url = unquote(actual_url)
                            parsed = urlparse(actual_url)
                            domain = parsed.netloc.replace('www.', '')
                            
                            if actual_url not in seen and len(seen) < max_results:
                                seen.add(actual_url)
                                leads.append({
                                    'company_name': domain,
                                    'url': actual_url,
                                    'location': location
                                })
                        except:
                            continue
            
            print(f"Google (Playwright) found {len(leads)} URLs")
            
    except Exception as e:
        print(f"Playwright search error: {e}")
    
    return leads

def search_leads_google(keywords, location, max_results=50):
    """
    Multi-method search with priority order:
    1. Google Custom Search API (official, most reliable)
    2. DuckDuckGo (less restrictive)
    3. Google with Playwright (browser automation)
    4. Fallback to example companies
    """
    leads = []
    
    # Method 1: Try Google Custom Search API first (best option)
    print("Trying Google Custom Search API...")
    leads = search_leads_google_api(keywords, location, max_results)
    
    # Method 2: Try DuckDuckGo if API didn't work
    if len(leads) == 0:
        print("Google API returned nothing, trying DuckDuckGo...")
        leads = search_leads_duckduckgo(keywords, location, max_results)
    
    # Method 3: If DuckDuckGo fails, try Google with Playwright
    if len(leads) == 0:
        print("DuckDuckGo returned nothing, trying Google with Playwright...")
        leads = search_leads_google_playwright(keywords, location, max_results)
    
    # Method 4: Fallback to example companies
    if len(leads) == 0:
        print("All search methods failed, using example companies...")
        example_urls = [
            'https://www.miraclehomehealthcareinc.com/',
            'https://assistedcares.com/',
            'https://www.rightathome.net/santa-barbara',
            'https://www.sbseniorcare.com/',
            'https://www.gentlebreezehomecarellc.com/',
            'https://helpinghg.com/',
            'https://vna.health/',
            'https://superiorseniorhomecare.com/',
            'https://superiorhh.com/'
        ]
        
        for url in example_urls[:max_results]:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            
            leads.append({
                'company_name': domain,
                'url': url,
                'location': location
            })
    
    return leads

def extract_contact_info(url, api_key=None):
    """
    Scrape a company website to extract contact information using Playwright.
    This bypasses most anti-bot protection by using a real browser.
    Returns dict with email and contact_name if found.
    """
    result = {'email': None, 'contact_name': None}
    
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Visit main page
            try:
                page.goto(url, timeout=15000, wait_until='domcontentloaded')
                page.wait_for_timeout(1000)  # Wait for content
                
                html = page.content()
                text = page.inner_text('body')
                
                # Look for email addresses
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                
                # Filter out common noise emails
                filtered_emails = [e for e in emails if not any(x in e.lower() for x in 
                    ['example.com', 'domain.com', 'email.com', 'sampleemail', 'youremail', 'yourmail'])]
                
                if filtered_emails:
                    result['email'] = filtered_emails[0]
                
                # If no email found on main page, try contact page
                if not result['email']:
                    soup = BeautifulSoup(html, 'html.parser')
                    contact_links = soup.find_all('a', href=True)
                    
                    for link in contact_links:
                        href = link.get('href', '').lower()
                        link_text = link.get_text(strip=True).lower()
                        
                        # Look for contact/about pages
                        if any(keyword in href or keyword in link_text for keyword in ['contact', 'about', 'team']):
                            contact_url = href
                            if not contact_url.startswith('http'):
                                from urllib.parse import urljoin
                                contact_url = urljoin(url, contact_url)
                            
                            try:
                                page.goto(contact_url, timeout=10000, wait_until='domcontentloaded')
                                page.wait_for_timeout(500)
                                contact_text = page.inner_text('body')
                                
                                contact_emails = re.findall(email_pattern, contact_text)
                                filtered_contact_emails = [e for e in contact_emails if not any(x in e.lower() for x in 
                                    ['example.com', 'domain.com', 'email.com'])]
                                
                                if filtered_contact_emails:
                                    result['email'] = filtered_contact_emails[0]
                                    break
                            except:
                                continue
                
                # Use LLM to extract contact name if API key provided and email found
                if api_key and result['email']:
                    try:
                        prompt = f"Extract the name of a senior executive or contact person from this text. Return ONLY the name, nothing else:\n\n{text[:2000]}"
                        contact_name = analyzer.chat_with_content(prompt, api_key).strip()
                        if len(contact_name) < 50 and contact_name:
                            result['contact_name'] = contact_name
                    except:
                        pass
                        
            except Exception as e:
                print(f"Playwright error for {url}: {str(e)[:100]}")
            
            browser.close()
            
    except Exception as e:
        print(f"Error extracting contact info from {url}: {str(e)[:100]}")
    
    return result

def send_email(to_email, subject, body, smtp_config):
    """
    Send an email using SMTP.
    
    smtp_config should have:
    - host: SMTP server (e.g., 'smtp.gmail.com')
    - port: SMTP port (e.g., 587)
    - username: SMTP username
    - password: SMTP password
    - from_email: Sender email address
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_config.get('from_email', smtp_config['username'])
        msg['To'] = to_email
        
        # Add body
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        return {'success': True}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def search_and_save_leads(keywords, location, api_key=None, max_results=50):
    """
    Search for leads and save them to the database.
    Also attempts to extract contact info for each lead.
    """
    print(f"Searching for: {keywords} in {location}")
    
    # Search for companies
    leads = search_leads_google(keywords, location, max_results)
    
    print(f"Found {len(leads)} potential leads")
    
    # Save leads and extract contact info
    saved_count = 0
    for lead in leads:
        # Extract contact info
        contact_info = extract_contact_info(lead['url'], api_key)
        
        # Save to database
        try:
            storage.save_lead(
                company_name=lead['company_name'],
                url=lead['url'],
                email=contact_info.get('email'),
                contact_name=contact_info.get('contact_name'),
                location=lead.get('location')
            )
            saved_count += 1
            email_status = contact_info.get('email', 'None')
            contact_status = contact_info.get('contact_name', 'None')
            print(f"Saved: {lead['company_name']} - Email: {email_status} - Contact: {contact_status}")
        except Exception as e:
            print(f"Error saving lead {lead['company_name']}: {e}")
        
        # Rate limiting to be polite
        time.sleep(random.uniform(1, 3))
    
    return {'saved': saved_count, 'total_found': len(leads)}
