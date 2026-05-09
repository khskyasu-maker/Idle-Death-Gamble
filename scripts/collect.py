import os
import time
import random
import requests
import urllib.robotparser
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import logger, get_data_path, load_json, save_json, get_kst_now

MAX_URLS_PER_RUN = 10

def can_fetch(url, user_agent):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Failed to parse robots.txt for {url}: {e}")
        return True # Default to True if robots.txt is missing or unreachable

def scrape_url(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    logger.info(f"Checking robots.txt for {url}...")
    if not can_fetch(url, user_agent):
        logger.warning(f"robots.txt disallowed fetching {url}")
        return {"status": "blocked_or_limited", "error_type": "robots.txt disallowed"}

    logger.info(f"Scraping {url}...")
    headers = {"User-Agent": user_agent}
    
    try:
        resp = requests.get(url, headers=headers, timeout=(5, 10))
        if resp.status_code in [401, 403, 429]:
            logger.warning(f"Received {resp.status_code} for {url}. Stopping requests for this domain.")
            return {"status": "blocked_or_limited", "error_type": f"HTTP {resp.status_code}"}
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # CAPTCHA 의심 응답 (Cloudflare 등)
        page_text_lower = soup.get_text().lower()
        if "captcha" in page_text_lower or "cloudflare" in page_text_lower:
            logger.warning(f"CAPTCHA suspected for {url}.")
            return {"status": "blocked_or_limited", "error_type": "CAPTCHA suspected"}
            
        title = soup.title.string if soup.title else ""
        text_content = soup.get_text(separator=' ', strip=True)
        text_snippet = text_content[:2000]
        
        keywords = ["1円", "1パチ", "エヴァ", "エヴァ15", "新世紀エヴァンゲリオン", "未来への咆哮", "甘デジ", "ライト", "ライトミドル", "ミドル"]
        found_keywords = [kw for kw in keywords if kw in text_content]
        
        return {
            "source": urlparse(url).netloc,
            "url": url,
            "status": "success",
            "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
            "page_title": title,
            "detected_update_date": "",
            "keywords_found": found_keywords,
            "text_snippet": text_snippet,
            "error_type": ""
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for {url}: {e}. Retrying once...")
        time.sleep(5)
        try:
            resp = requests.get(url, headers=headers, timeout=(5, 10))
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            title = soup.title.string if soup.title else ""
            text_snippet = soup.get_text(separator=' ', strip=True)[:2000]
            return {
                "source": urlparse(url).netloc,
                "url": url,
                "status": "success",
                "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
                "page_title": title,
                "detected_update_date": "",
                "keywords_found": [],
                "text_snippet": text_snippet,
                "error_type": ""
            }
        except Exception as retry_e:
            return {"status": "failed", "error_type": str(retry_e)}
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return {"status": "failed", "error_type": str(e)}

def main():
    stores_data = load_json(get_data_path('stores.json'), {})
    stores = stores_data.get('stores', []) if isinstance(stores_data, dict) else stores_data
    
    # Check if we should fallback
    collected_path = get_data_path('collected.json')
    results = load_json(collected_path, {})
    
    now = get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST")
    urls_processed = 0

    for store in stores:
        if urls_processed >= MAX_URLS_PER_RUN:
            logger.info("Reached maximum URLs per run limit.")
            break
            
        store_id = store['id']
        logger.info(f"Processing store: {store['name']}")
        
        if store_id not in results:
            results[store_id] = {
                "store_name": store['name'],
                "checked_at": now,
                "links_data": {}
            }
        else:
            results[store_id]["checked_at"] = now
            
        links = store.get('links', {})
        for link_type, url in links.items():
            if urls_processed >= MAX_URLS_PER_RUN:
                break
                
            if not url:
                results[store_id]["links_data"][link_type] = {"status": "skipped", "error_type": "No URL"}
                continue
            
            data = scrape_url(url)
            results[store_id]["links_data"][link_type] = data
            urls_processed += 1
            
            sleep_time = random.uniform(5.0, 10.0)
            logger.info(f"Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    save_json(results, collected_path)
    logger.info("Collection finished.")

if __name__ == "__main__":
    main()
