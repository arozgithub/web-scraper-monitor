import os
import time
import json
import random
from playwright.sync_api import sync_playwright

SESSION_FILE = 'linkedin_session.json'

def login_and_save_session():
    """
    Opens a browser for the user to log in manually.
    Saves the session state (cookies, local storage) to a file.
    """
    with sync_playwright() as p:
        # Launch headful browser for user interaction
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to LinkedIn login page...")
        page.goto("https://www.linkedin.com/login")
        
        print("Please log in manually in the browser window.")
        print("Waiting for successful login (any LinkedIn page except login/authwall)...")
        
        # Wait for user to complete login (timeout 5 minutes)
        try:
            # Wait for URL to change away from login page
            start_time = time.time()
            while time.time() - start_time < 300:  # 5 minute timeout
                try:
                    current_url = page.url
                    print(f"Checking URL: {current_url}") # Debug
                    
                    # Check for Global Nav (strong indicator of being logged in)
                    # The global nav usually has class 'global-nav' or id 'global-nav'
                    is_logged_in = False
                    try:
                        if page.locator(".global-nav, #global-nav").count() > 0:
                            is_logged_in = True
                    except:
                        pass
                    
                    # Fallback to URL check if element check fails
                    if not is_logged_in:
                         if "linkedin.com" in current_url and "login" not in current_url and "authwall" not in current_url and "checkpoint" not in current_url:
                             is_logged_in = True

                    if is_logged_in:
                        print(f"Login detected! Saving session...")
                        
                        # Save storage state
                        context.storage_state(path=SESSION_FILE)
                        print(f"Session saved to {SESSION_FILE}")
                        
                        # Give user a moment to see success
                        try:
                            page.evaluate("alert('Session saved! Closing in 3 seconds...')")
                            time.sleep(3)
                        except:
                            pass
                        
                        browser.close()
                        return True
                    
                    time.sleep(1)
                except Exception as e:
                    if "Target closed" in str(e) or "browser has been closed" in str(e):
                        print("Browser was closed manually before session was saved!")
                        return False
                    raise e
            
            print("Login timeout - 5 minutes elapsed")
            return False
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
            
            print("Login timeout - 5 minutes elapsed")
            return False
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
        finally:
            try:
                browser.close()
            except:
                pass
            
    return True

def scrape_linkedin_page(url, headless=True):
    """
    Scrapes a LinkedIn profile or company page using the saved session.
    """
    if not os.path.exists(SESSION_FILE):
        return {"error": "No session file found. Please login first."}
        
    data = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            # Load session
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            
            # Randomize user agent slightly to avoid detection (optional)
            # context.set_extra_http_headers({"User-Agent": "Mozilla/5.0 ..."})
            
            print(f"Navigating to {url}...")
            page.goto(url)
            
            # Random delay
            time.sleep(random.uniform(2, 5))
            
            # Check if we are on auth wall
            if "authwall" in page.url or "login" in page.url:
                return {"error": "Session expired or auth wall hit. Please login again."}
            
            # Extract Data based on URL type
            if "/in/" in url:
                data = _extract_profile_data(page)
                data['type'] = 'profile'
            elif "/company/" in url:
                data = _extract_company_data(page)
                data['type'] = 'company'
            else:
                data = {"error": "Unknown LinkedIn URL type"}
                
            data['url'] = url
            
        except Exception as e:
            data = {"error": str(e)}
        finally:
            browser.close()
            
    return data

def _extract_profile_data(page):
    """Extract data from a profile page."""
    data = {}
    
    # Name
    try:
        data['name'] = page.locator("h1").first.inner_text()
    except:
        data['name'] = "Unknown"
        
    # Headline
    try:
        data['headline'] = page.locator(".text-body-medium.break-words").first.inner_text()
    except:
        data['headline'] = ""
        
    # Location
    try:
        data['location'] = page.locator(".text-body-small.inline.t-black--light.break-words").first.inner_text()
    except:
        data['location'] = ""
        
    # About
    try:
        # Click "see more" if present
        # page.locator("...").click() # simplified for now
        data['about'] = page.locator("#about").locator("..").locator(".display-flex .inline-show-more-text").inner_text()
    except:
        data['about'] = ""
        
    # Experience (Simple extraction)
    try:
        # This is tricky as selectors change. Just getting text of the section.
        exp_section = page.locator("#experience").locator("..")
        data['experience_raw'] = exp_section.inner_text()
    except:
        data['experience_raw'] = ""
        
    return data

def _extract_company_data(page):
    """Extract data from a company page."""
    data = {}
    
    # Basic Info
    try:
        data['name'] = page.locator("h1").first.inner_text()
    except:
        data['name'] = "Unknown"
        
    try:
        # Try to find the tagline or about text
        data['about'] = page.locator("p.break-words").first.inner_text()
    except:
        data['about'] = ""

    # Extract details from the "About" section (usually on the main page or About tab)
    # We'll try to click "About" tab if we are not there, or just scrape what's visible
    try:
        # Look for the organization details dl/dt/dd structure or similar
        # This is hard to get perfectly without specific selectors, but we can try to get the whole text block
        about_section = page.locator("section").filter(has_text="Overview").first
        if about_section.count() > 0:
             data['overview'] = about_section.inner_text()
    except:
        pass

    # Scrape Posts
    print("Scraping posts...")
    data['posts'] = []
    try:
        # Construct posts URL (more reliable than clicking)
        current_url = page.url
        if "/company/" in current_url:
            # Ensure we don't double append /posts/
            base_url = current_url.split("/posts/")[0].split("?")[0]
            if not base_url.endswith("/"):
                base_url += "/"
            posts_url = base_url + "posts/?feedView=all"
            
            page.goto(posts_url)
            time.sleep(3) # Wait for feed to load
            
            # Scroll down a bit to trigger loading
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(2)
            
            # Extract posts
            # Posts are usually in 'div.feed-shared-update-v2' or similar
            post_elements = page.locator(".feed-shared-update-v2, .occludable-update").all()
            
            for i, post in enumerate(post_elements[:5]): # Get last 5 posts
                post_data = {}
                try:
                    # Text content
                    text_elem = post.locator(".feed-shared-update-v2__description, .feed-shared-text, .update-components-text")
                    if text_elem.count() > 0:
                        post_data['text'] = text_elem.first.inner_text()
                    
                    # Likes/Reactions count
                    likes_elem = post.locator(".social-details-social-counts__reactions-count")
                    if likes_elem.count() > 0:
                        post_data['likes'] = likes_elem.first.inner_text()
                        
                    # Date (e.g. "2d", "1w")
                    date_elem = post.locator(".update-components-actor__sub-description")
                    if date_elem.count() > 0:
                        post_data['date'] = date_elem.first.inner_text().split("•")[0].strip()
                        
                    if post_data:
                        data['posts'].append(post_data)
                except Exception as e:
                    print(f"Error extracting post {i}: {e}")
                    
    except Exception as e:
        print(f"Error scraping posts: {e}")
        data['posts_error'] = str(e)
        
    return data
