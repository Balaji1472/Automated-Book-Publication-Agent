# Way 1: requests + beautifulsoup 
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urlparse
import time

def scrape_chapter_requests(url: str) -> dict:
    """
    Scrape content using requests + BeautifulSoup (Windows-friendly).
    Returns a dictionary with url, content, and metadata.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        os.makedirs("scraping/output", exist_ok=True)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content = extract_content_by_site_bs4(soup, url)
        
        title = soup.title.string if soup.title else "No title found"
        
        scraped_data = {
            "url": url,
            "title": title.strip(),
            "content": content,
            "word_count": len(content.split()),
            "status": "success"
        }
        

        with open("scraping/output/latest_scrape.json", "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, indent=4, ensure_ascii=False)
        
        return scraped_data
        
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "title": "Error",
            "content": f"Error scraping content: Network error - {str(e)}",
            "word_count": 0,
            "status": "error",
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "url": url,
            "title": "Error",
            "content": f"Error scraping content: {str(e)}",
            "word_count": 0,
            "status": "error",
            "error": str(e)
        }

def extract_content_by_site_bs4(soup, url: str) -> str:
    """
    Extract content based on the website structure using BeautifulSoup.
    Handles different sites with different selectors.
    """
    domain = urlparse(url).netloc.lower()
    

    if "wikisource.org" in domain:
        try:
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if content_div:
                for nav in content_div.find_all(['div', 'span'], class_=re.compile(r'nav|header|footer')):
                    nav.decompose()
                content = content_div.get_text()
                if content.strip():
                    return clean_text(content)
        except:
            pass
    
    elif "gutenberg.org" in domain:
        try:

            content_selectors = ['pre', '.chapter', 'body']
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text()
                    if content.strip() and len(content) > 100:
                        return clean_text(content)
        except:
            pass
    

    elif "archive.org" in domain:
        try:
            content_selectors = ['.textLayer', '.BookReader', '.book-text', 'pre']
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text()
                    if content.strip() and len(content) > 100:
                        return clean_text(content)
        except:
            pass
    
    selectors = [
        'article',
        'main',
        '.content',
        '#content',
        '.post-content',
        '.entry-content',
        '.chapter-content',
        '.text-content',
        'body'
    ]
    
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:

                for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    unwanted.decompose()
                
                content = element.get_text()
                if content.strip() and len(content) > 100:  
                    return clean_text(content)
        except:
            continue
    

    try:
        body = soup.find('body')
        if body:

            for unwanted in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                unwanted.decompose()
            return clean_text(body.get_text())
    except:
        pass
    
    return "Unable to extract content from this URL."

# Way 2: playwright
def scrape_chapter_playwright_fixed(url: str) -> dict:
    """
    Fixed Playwright version with proper Windows handling.
    """
    try:
        import asyncio
        import sys
        
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions'
                ]
            )
            
            page = browser.new_page()
            
            page.set_default_timeout(30000) 
            
            page.goto(url, wait_until="networkidle")
            
            os.makedirs("scraping/output/screenshots", exist_ok=True)

            page.screenshot(path="scraping/output/screenshots/latest_scrape.png", full_page=True)
            
            content = extract_content_by_site_playwright(page, url)
            
            
            title = page.title()
            
            browser.close()
            
         
            scraped_data = {
                "url": url,
                "title": title,
                "content": content,
                "word_count": len(content.split()),
                "status": "success"
            }
            
            
            with open("scraping/output/latest_scrape.json", "w", encoding="utf-8") as f:
                json.dump(scraped_data, f, indent=4, ensure_ascii=False)
            
            return scraped_data
            
    except Exception as e:
        return {
            "url": url,
            "title": "Error",
            "content": f"Error scraping content: {str(e)}",
            "word_count": 0,
            "status": "error",
            "error": str(e)
        }

def extract_content_by_site_playwright(page, url: str) -> str:
    """
    Extract content based on the website structure using Playwright.
    """
    domain = urlparse(url).netloc.lower()
    
    if "wikisource.org" in domain:
        try:
            content = page.locator("#mw-content-text").inner_text()
            if content.strip():
                return clean_text(content)
        except:
            pass
    
    elif "gutenberg.org" in domain:
        try:
            content = page.locator("body").inner_text()
            if content.strip():
                return clean_text(content)
        except:
            pass
    
    elif "archive.org" in domain:
        try:
            content = page.locator(".textLayer, .BookReader, .book-text").inner_text()
            if content.strip():
                return clean_text(content)
        except:
            pass
    
    selectors = [
        "article",
        "main",
        ".content",
        "#content",
        ".post-content",
        ".entry-content",
        ".chapter-content",
        "body"
    ]
    
    for selector in selectors:
        try:
            content = page.locator(selector).first.inner_text()
            if content.strip() and len(content) > 100:
                return clean_text(content)
        except:
            continue
    
    try:
        return clean_text(page.locator("body").inner_text())
    except:
        return "Unable to extract content from this URL."

def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    """
    if not text:
        return ""
    
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not is_navigation_line(line):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def is_navigation_line(line: str) -> bool:
    """
    Check if a line is likely navigation/menu content.
    """
    nav_patterns = [
        r'^(home|menu|navigation|contents|index|search|login|register)$',
        r'^(next|previous|back|forward|chapter \d+)$',
        r'^(←|→|«|»)',
        r'^\d+$',  
        r'^(edit|view|history|talk|discussion)$'
    ]
    
    line_lower = line.lower()
    for pattern in nav_patterns:
        if re.match(pattern, line_lower):
            return True
    
    return False

def validate_url(url: str) -> bool:
    """
    Basic URL validation.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Main function that tries both methods
def scrape_chapter(url: str) -> dict:
    """
    Main scraping function that tries requests first, then Playwright as fallback.
    """
    print(f"🔄 Attempting to scrape: {url}")
    
    try:
        print("📡 Trying requests + BeautifulSoup method...")
        result = scrape_chapter_requests(url)
        if result["status"] == "success" and len(result["content"]) > 100:
            print("✅ Successfully scraped with requests method")
            return result
    except Exception as e:
        print(f"❌ Requests method failed: {e}")
    
    try:
        print("🎭 Falling back to Playwright method...")
        result = scrape_chapter_playwright_fixed(url)
        if result["status"] == "success":
            print("✅ Successfully scraped with Playwright method")
            return result
    except Exception as e:
        print(f"❌ Playwright method also failed: {e}")
    
    return {
        "url": url,
        "title": "Error",
        "content": "Unable to scrape content. Both methods failed.",
        "word_count": 0,
        "status": "error",
        "error": "All scraping methods failed"
    }

if __name__ == "__main__":
    test_url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_2"
    result = scrape_chapter(test_url)
    print(f"✅ Scraping completed. Status: {result['status']}")
    print(f"Content length: {len(result['content'])} characters")