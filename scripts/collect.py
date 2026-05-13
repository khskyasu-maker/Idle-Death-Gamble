import os
import re
import time
import random
import requests
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils import logger, get_data_path, load_json, save_json, get_kst_now

MAX_URLS_PER_RUN = 10
PROVIDER_PARSER_VERSION = 2
KEYWORDS = ["1円", "1パチ", "エヴァ", "エヴァ15", "新世紀エヴァンゲリオン", "未来への咆哮", "甘デジ", "ライト", "ライトミドル", "ミドル"]
TRANSIENT_ERROR_MARKERS = (
    "ProxyError",
    "NameResolutionError",
    "Temporary failure in name resolution",
    "Failed to resolve",
    "Tunnel connection failed",
    "Read timed out",
    "ConnectTimeout",
    "ConnectionError",
    "Max retries exceeded",
    "HTTP 401",
    "HTTP 403",
    "HTTP 429",
    "CAPTCHA suspected",
)
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
MACHINE_DETAIL_MARKERS = ["台番号", "総回転", "差玉", "大当り回数", "スランプグラフ"]
PROVIDER_CANDIDATE_LINK_MARKERS = (
    "番台",
    "detail",
    "machine",
    "unit",
    "history",
    "graph",
    "slump",
    "機種",
    "台番号",
    "ランキング",
    "all_list",
    "ranking",
    "psmodelnamesearch",
    "maxdetail",
)
PROVIDER_MACHINE_SEARCH_MARKERS = (
    "機種別",
    "機種名",
    "machine",
    "model",
    "psmodelnamesearch",
)
PROVIDER_UNIT_SEARCH_MARKERS = (
    "台番号",
    "番台",
    "all_list",
    "unit=",
)
PROVIDER_RANKING_MARKERS = (
    "ランキング",
    "ranking",
)
PROVIDER_DETAIL_MARKERS = (
    "detail",
    "history",
    "graph",
    "slump",
    "maxdetail",
    "大当り",
    "総回転",
    "差玉",
)
PROVIDER_PACHINKO_SECTION_MARKERS = (
    "パチンコ",
    "ぱちんこ",
    "Pachinko",
)
PROVIDER_SLOT_SECTION_MARKERS = (
    "スロット",
    "Slot",
)
MACHINE_TEXT_MARKERS = (
    "の機種情報 更新日",
    "機種情報（パチンコ）",
    "機種名 新台増台",
    "機種名",
    "パチンコ [",
    "【1",
    "【100円",
    "【4",
)

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

def slugify_key(value):
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")

def machine_source_key(index, source):
    provider = slugify_key(source.get("provider", "source"))
    kind = slugify_key(source.get("kind", "machine_data"))
    return f"{index:02d}_{provider}_{kind}"

def extract_dmm_jackpot_summary(soup, url, text_content):
    parsed_url = urlparse(url)
    if parsed_url.netloc != "p-town.dmm.com" or not parsed_url.path.endswith("/jackpot"):
        return {}

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    store_name = ""
    title_match = re.search(r"【大当りデータ情報】(.+?)の最新台データ情報", title)
    if title_match:
        store_name = title_match.group(1)

    latest_update = ""
    latest_update_el = soup.select_one(".shop-jackpot-note .latest-update-date")
    if latest_update_el:
        latest_update = latest_update_el.get_text(" ", strip=True)

    iframe_provider_url = ""
    for script in soup.find_all("script"):
        script_text = script.string or script.get_text()
        iframe_match = re.search(r"iframe\.src\s*=\s*['\"]([^'\"]+)['\"]", script_text)
        if iframe_match:
            iframe_provider_url = iframe_match.group(1)
            break

    machine_links = []
    seen_machine_urls = set()
    for link in soup.select('a[href^="/machines/"]'):
        href = urljoin(url, link.get("href", ""))
        name = link.get_text(" ", strip=True)
        if href in seen_machine_urls:
            continue
        seen_machine_urls.add(href)
        machine_links.append({"name": name, "url": href})

    static_detail_markers = [marker for marker in MACHINE_DETAIL_MARKERS if marker in text_content]

    provider_domain = urlparse(iframe_provider_url).netloc if iframe_provider_url else ""
    notes = "DMM jackpot page is web-accessible, but per-unit data collection is out of scope."
    if iframe_provider_url:
        notes += " External iframe provider is recorded as manual reference only."
    if not static_detail_markers:
        notes += " Static HTML is not used for 台番号(기기 번호)-level values."

    return {
        "page_type": "dmm_jackpot",
        "store_name": store_name,
        "latest_update_text": latest_update,
        "has_dedama_iframe": bool(soup.select_one("iframe.dedama-iframe")),
        "iframe_provider_url": iframe_provider_url,
        "iframe_provider_domain": provider_domain,
        "static_machine_link_count": len(machine_links),
        "static_machine_links_sample": machine_links[:10],
        "target_keywords_found": [kw for kw in KEYWORDS if kw in text_content],
        "static_detail_markers_found": static_detail_markers,
        "static_machine_detail_available": bool(static_detail_markers),
        "notes": notes,
    }


def classify_provider_link(href, label):
    combined = f"{href} {label}"
    combined_lower = combined.lower()
    categories = []

    if any(marker.lower() in combined_lower for marker in PROVIDER_MACHINE_SEARCH_MARKERS):
        categories.append("machine_search")
    if (
        any(marker.lower() in combined_lower for marker in PROVIDER_UNIT_SEARCH_MARKERS)
        or re.search(r"\d+\s*番", label)
    ):
        categories.append("unit_search")
    if any(marker.lower() in combined_lower for marker in PROVIDER_RANKING_MARKERS):
        categories.append("ranking")
    if any(marker.lower() in combined_lower for marker in PROVIDER_DETAIL_MARKERS):
        categories.append("detail")

    return categories


def detect_provider_sections(text_content):
    sections = []
    if any(marker in text_content for marker in PROVIDER_PACHINKO_SECTION_MARKERS):
        sections.append("pachinko")
    if any(marker in text_content for marker in PROVIDER_SLOT_SECTION_MARKERS):
        sections.append("slot")

    if "pachinko" in sections and "slot" in sections:
        machine_scope = "mixed"
    elif "pachinko" in sections:
        machine_scope = "pachinko"
    elif "slot" in sections:
        machine_scope = "slot_only"
    else:
        machine_scope = "unknown"

    return sections, machine_scope


def categorize_provider_link_records(records):
    categorized = []
    machine_search_links = []
    unit_search_links = []
    ranking_links = []
    detail_links = []

    for record in records:
        label = record.get("label", "")
        href = record.get("url", "")
        categories = record.get("categories") or classify_provider_link(href, label)
        if not categories:
            continue
        categorized_record = {
            "label": label[:120],
            "url": href,
            "categories": categories,
        }
        categorized.append(categorized_record)
        if "machine_search" in categories:
            machine_search_links.append(categorized_record)
        if "unit_search" in categories:
            unit_search_links.append(categorized_record)
        if "ranking" in categories:
            ranking_links.append(categorized_record)
        if "detail" in categories:
            detail_links.append(categorized_record)

    return {
        "candidate_links_sample": categorized[:10],
        "machine_search_link_count": len(machine_search_links),
        "machine_search_links_sample": machine_search_links[:5],
        "unit_search_link_count": len(unit_search_links),
        "unit_search_links_sample": unit_search_links[:5],
        "ranking_link_count": len(ranking_links),
        "ranking_links_sample": ranking_links[:5],
        "detail_link_count": len(detail_links),
        "detail_links_sample": detail_links[:5],
    }


def backfill_provider_access_summary(provider_access):
    if not isinstance(provider_access, dict):
        return provider_access
    if provider_access.get("provider_parser_version") == PROVIDER_PARSER_VERSION:
        return provider_access

    backfilled = dict(provider_access)
    categorized = categorize_provider_link_records(backfilled.get("candidate_links_sample", []))
    sections, machine_scope = detect_provider_sections(backfilled.get("text_snippet", ""))
    backfilled.update(categorized)
    backfilled["candidate_link_count"] = len(categorized["candidate_links_sample"])
    backfilled["candidate_link_count_is_sample_based"] = True
    backfilled["provider_sections_found"] = sections
    backfilled["provider_machine_scope"] = machine_scope
    backfilled["provider_parser_version"] = PROVIDER_PARSER_VERSION
    backfilled["provider_parser_backfilled_from"] = "candidate_links_sample"
    backfilled["can_attempt_unit_list_parse"] = bool(backfilled.get("unit_search_link_count"))
    return backfilled


def summarize_provider_html(resp, url):
    soup = BeautifulSoup(resp.content, "html.parser")
    text_content = soup.get_text(separator=" ", strip=True)
    detail_markers = [marker for marker in MACHINE_DETAIL_MARKERS if marker in text_content]
    candidate_links = []
    machine_search_links = []
    unit_search_links = []
    ranking_links = []
    detail_links = []
    seen_urls = set()

    for link in soup.find_all("a"):
        href = link.get("href", "")
        label = link.get_text(" ", strip=True)
        absolute_url = urljoin(url, href)
        combined = f"{href} {label}".lower()
        categories = classify_provider_link(href, label)
        if not categories and not any(marker.lower() in combined for marker in PROVIDER_CANDIDATE_LINK_MARKERS):
            continue
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)
        record = {
            "label": label[:120],
            "url": absolute_url,
            "categories": categories,
        }
        candidate_links.append(record)
        if "machine_search" in categories:
            machine_search_links.append(record)
        if "unit_search" in categories:
            unit_search_links.append(record)
        if "ranking" in categories:
            ranking_links.append(record)
        if "detail" in categories:
            detail_links.append(record)

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    provider_sections_found, provider_machine_scope = detect_provider_sections(text_content)

    return {
        "provider_parser_version": PROVIDER_PARSER_VERSION,
        "page_title": title,
        "detail_markers_found": detail_markers,
        "static_machine_detail_available": bool(detail_markers),
        "candidate_link_count": len(candidate_links),
        "candidate_links_sample": candidate_links[:10],
        "machine_search_link_count": len(machine_search_links),
        "machine_search_links_sample": machine_search_links[:5],
        "unit_search_link_count": len(unit_search_links),
        "unit_search_links_sample": unit_search_links[:5],
        "ranking_link_count": len(ranking_links),
        "ranking_links_sample": ranking_links[:5],
        "detail_link_count": len(detail_links),
        "detail_links_sample": detail_links[:5],
        "target_keywords_found": [kw for kw in KEYWORDS if kw in text_content],
        "provider_sections_found": provider_sections_found,
        "provider_machine_scope": provider_machine_scope,
        "can_attempt_unit_list_parse": bool(unit_search_links),
        "text_snippet": text_content[:500],
    }

def probe_iframe_provider_access(url):
    if not url:
        return {
            "status": "skipped",
            "access_status": "no_url",
            "error_type": "No iframe provider URL",
        }

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    base = {
        "url": url,
        "source": urlparse(url).netloc,
        "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
    }

    logger.info(f"Checking robots.txt for iframe provider {url}...")
    if not can_fetch(url, user_agent):
        logger.warning(f"robots.txt disallowed fetching iframe provider {url}")
        return {
            **base,
            "status": "blocked_or_limited",
            "access_status": "robots_disallowed",
            "error_type": "robots.txt disallowed",
        }

    headers = {"User-Agent": user_agent}
    logger.info(f"Probing iframe provider {url}...")
    try:
        resp = requests.get(url, headers=headers, timeout=(5, 10), allow_redirects=False)
        provider_data = {
            **base,
            "status": "success",
            "access_status": f"http_{resp.status_code}",
            "http_status": resp.status_code,
            "content_type": resp.headers.get("Content-Type", ""),
            "error_type": "",
        }

        if resp.status_code in REDIRECT_STATUS_CODES:
            provider_data.update({
                "status": "redirect",
                "redirect_to": resp.headers.get("Location", ""),
            })
            return provider_data

        if resp.status_code in [401, 403, 429]:
            provider_data.update({
                "status": "blocked_or_limited",
                "error_type": f"HTTP {resp.status_code}",
            })
            return provider_data

        if resp.status_code == 404:
            provider_data.update({
                "status": "not_found",
                "error_type": "HTTP 404",
            })
            return provider_data

        if resp.status_code >= 400:
            provider_data.update({
                "status": "failed",
                "error_type": f"HTTP {resp.status_code}",
            })
            return provider_data

        content_type = resp.headers.get("Content-Type", "")
        if "html" in content_type.lower() or not content_type:
            provider_data.update(summarize_provider_html(resp, url))
        return provider_data
    except requests.exceptions.RequestException as e:
        return {
            **base,
            "status": "failed",
            "access_status": "network_failed",
            "error_type": str(e),
        }


def build_machine_text_snippet(text_content, window=6000, limit=12000):
    positions = []
    for marker in MACHINE_TEXT_MARKERS:
        positions.extend(match.start() for match in re.finditer(re.escape(marker), text_content))

    if not positions:
        return ""

    snippets = []
    covered_until = -1
    for position in sorted(set(positions)):
        if position < covered_until:
            continue
        start = max(0, position - 200)
        end = min(len(text_content), position + window)
        snippets.append(text_content[start:end])
        covered_until = end
        if sum(len(snippet) for snippet in snippets) >= limit:
            break

    return "\n...\n".join(snippets)[:limit]


def parse_html_response(resp, url):
    soup = BeautifulSoup(resp.content, 'html.parser')

    page_text_lower = soup.get_text().lower()
    if "captcha" in page_text_lower or "cloudflare" in page_text_lower:
        logger.warning(f"CAPTCHA suspected for {url}.")
        return {
            "source": urlparse(url).netloc,
            "url": url,
            "status": "blocked_or_limited",
            "access_status": "captcha_suspected",
            "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
            "error_type": "CAPTCHA suspected",
        }

    title = soup.title.string if soup.title else ""
    text_content = soup.get_text(separator=' ', strip=True)
    text_snippet = text_content[:2000]
    machine_text_snippet = build_machine_text_snippet(text_content)
    found_keywords = [kw for kw in KEYWORDS if kw in text_content]

    data = {
        "source": urlparse(url).netloc,
        "url": url,
        "status": "success",
        "access_status": f"http_{resp.status_code}",
        "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "page_title": title,
        "detected_update_date": "",
        "keywords_found": found_keywords,
        "text_snippet": text_snippet,
        "machine_text_snippet": machine_text_snippet,
        "content_type": resp.headers.get("Content-Type", ""),
        "error_type": "",
    }
    jackpot_summary = extract_dmm_jackpot_summary(soup, url, text_content)
    if jackpot_summary:
        if jackpot_summary.get("iframe_provider_url"):
            jackpot_summary["provider_access"] = {
                "status": "manual_reference_only",
                "access_status": "provider_crawling_out_of_scope",
                "url": jackpot_summary["iframe_provider_url"],
                "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
                "error_type": "",
            }
        data["machine_data_page"] = jackpot_summary
    return data

def probe_source_url(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    logger.info(f"Checking robots.txt for machine-data source {url}...")
    if not can_fetch(url, user_agent):
        logger.warning(f"robots.txt disallowed fetching {url}")
        return {
            "source": urlparse(url).netloc,
            "url": url,
            "status": "blocked_or_limited",
            "access_status": "robots_disallowed",
            "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
            "error_type": "robots.txt disallowed",
        }

    headers = {"User-Agent": user_agent}
    logger.info(f"Probing machine-data source {url}...")

    try:
        resp = requests.get(url, headers=headers, timeout=(5, 10), allow_redirects=False)
        status_code = resp.status_code
        base = {
            "source": urlparse(url).netloc,
            "url": url,
            "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
            "http_status": status_code,
            "content_type": resp.headers.get("Content-Type", ""),
        }

        if status_code in REDIRECT_STATUS_CODES:
            return {
                **base,
                "status": "redirect",
                "access_status": f"http_{status_code}_redirect",
                "redirect_to": resp.headers.get("Location", ""),
                "error_type": "",
            }

        if status_code in [401, 403, 429]:
            logger.warning(f"Received {status_code} for machine-data source {url}.")
            return {
                **base,
                "status": "blocked_or_limited",
                "access_status": f"http_{status_code}",
                "error_type": f"HTTP {status_code}",
            }

        if status_code == 404:
            return {
                **base,
                "status": "not_found",
                "access_status": "http_404",
                "error_type": "HTTP 404",
            }

        if status_code >= 400:
            return {
                **base,
                "status": "failed",
                "access_status": f"http_{status_code}",
                "error_type": f"HTTP {status_code}",
            }

        parsed = parse_html_response(resp, url)
        parsed.update(base)
        return parsed
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for machine-data source {url}: {e}. Retrying once...")
        time.sleep(5)
        try:
            resp = requests.get(url, headers=headers, timeout=(5, 10), allow_redirects=False)
            if resp.status_code == 404:
                return {
                    "source": urlparse(url).netloc,
                    "url": url,
                    "status": "not_found",
                    "access_status": "http_404",
                    "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
                    "http_status": 404,
                    "error_type": "HTTP 404",
                }
            resp.raise_for_status()
            parsed = parse_html_response(resp, url)
            parsed["http_status"] = resp.status_code
            return parsed
        except Exception as retry_e:
            return {
                "source": urlparse(url).netloc,
                "url": url,
                "status": "failed",
                "access_status": "network_failed",
                "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
                "error_type": str(retry_e),
            }

def probe_machine_source(source):
    url = source.get("url", "")
    if not url:
        return {"status": "skipped", "access_status": "no_url", "error_type": "No URL"}

    return {
        "source": urlparse(url).netloc,
        "url": url,
        "status": "manual_reference_only",
        "access_status": source.get("access_status", "manual_required"),
        "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "error_type": "",
        "notes": "Per-unit provider crawling is out of scope. Use data/namba-actual-1yen-lineup.json for corrected Namba low-rate machine information.",
    }

def find_collected_url_data(links_data, url):
    for data in links_data.values():
        if isinstance(data, dict) and data.get("url") == url and data.get("status") != "skipped":
            return dict(data)
    return None

def is_manual_machine_source(source):
    declared_access = source.get("access_status", "").lower()
    return "app" in declared_access or source.get("kind") == "machine_data_notice"

def collection_sort_key(data):
    if not isinstance(data, dict):
        return ""
    if data.get("status") == "skipped":
        return "9999-99-99 99:99:99 KST"
    return data.get("checked_at") or data.get("last_attempt_at") or ""

def collection_sort_key_for_url(data, url):
    if isinstance(data, dict) and data.get("url") and data.get("url") != url:
        return ""
    if (
        isinstance(data, dict)
        and urlparse(url).netloc == "p-town.dmm.com"
        and urlparse(url).path.endswith("/jackpot")
        and data.get("status") == "success"
        and (
            not data.get("machine_data_page")
            or (
                data.get("machine_data_page", {}).get("iframe_provider_url")
                and not data.get("machine_data_page", {}).get("provider_access")
            )
            or (
                data.get("machine_data_page", {}).get("provider_access", {}).get("status") == "success"
                and data.get("machine_data_page", {}).get("provider_access", {}).get("provider_parser_version") != PROVIDER_PARSER_VERSION
                and data.get("machine_data_page", {}).get("provider_access", {}).get("last_provider_parser_version_attempted") != PROVIDER_PARSER_VERSION
            )
        )
    ):
        return ""
    return collection_sort_key(data)

def ensure_store_result(results, store):
    store_id = store["id"]
    if store_id not in results or not isinstance(results[store_id], dict):
        results[store_id] = {
            "store_name": store["name"],
            "checked_at": "Unknown",
            "links_data": {},
            "machine_data_sources": {}
        }
    else:
        results[store_id]["store_name"] = store["name"]
        results[store_id].setdefault("checked_at", "Unknown")
        results[store_id].setdefault("links_data", {})
        results[store_id].setdefault("machine_data_sources", {})

def prepare_non_request_entries(results, stores, now):
    for store in stores:
        ensure_store_result(results, store)
        store_result = results[store["id"]]

        for link_type, url in store.get("links", {}).items():
            if not url:
                store_result["links_data"][link_type] = {
                    "status": "skipped",
                    "error_type": "No URL",
                }

        for source_index, source in enumerate(store.get("machine_data", {}).get("sources", [])):
            key = machine_source_key(source_index, source)
            if not source.get("url"):
                store_result["machine_data_sources"][key] = {
                    "status": "skipped",
                    "access_status": "no_url",
                    "error_type": "No URL",
                    "provider": source.get("provider", ""),
                    "kind": source.get("kind", ""),
                    "declared_access_status": source.get("access_status", ""),
                    "notes": source.get("notes", ""),
                }
            else:
                data = probe_machine_source(source)
                data["provider"] = source.get("provider", "")
                data["kind"] = source.get("kind", "")
                data["declared_access_status"] = source.get("access_status", "")
                data["notes"] = source.get("notes", "")
                store_result["machine_data_sources"][key] = data
                store_result["checked_at"] = now

def build_collection_tasks(stores, results):
    tasks = []
    order = 0
    for store in stores:
        ensure_store_result(results, store)
        store_id = store["id"]
        store_result = results[store_id]

        for link_type, url in store.get("links", {}).items():
            if not url:
                continue
            existing_data = store_result.get("links_data", {}).get(link_type, {})
            tasks.append({
                "order": order,
                "type": "link",
                "store": store,
                "link_type": link_type,
                "url": url,
                "sort_key": collection_sort_key_for_url(existing_data, url),
            })
            order += 1

    return sorted(tasks, key=lambda task: (task["sort_key"], task["order"]))

def scrape_url(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    logger.info(f"Checking robots.txt for {url}...")
    if not can_fetch(url, user_agent):
        logger.warning(f"robots.txt disallowed fetching {url}")
        return {
            "source": urlparse(url).netloc,
            "url": url,
            "status": "blocked_or_limited",
            "access_status": "robots_disallowed",
            "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
            "error_type": "robots.txt disallowed",
        }

    logger.info(f"Scraping {url}...")
    headers = {"User-Agent": user_agent}

    try:
        resp = requests.get(url, headers=headers, timeout=(5, 10))
        if resp.status_code in [401, 403, 429]:
            logger.warning(f"Received {resp.status_code} for {url}. Stopping requests for this domain.")
            return {
                "source": urlparse(url).netloc,
                "url": url,
                "status": "blocked_or_limited",
                "access_status": f"http_{resp.status_code}",
                "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
                "error_type": f"HTTP {resp.status_code}",
            }
        resp.raise_for_status()

        data = parse_html_response(resp, url)
        data["access_status"] = data.get("access_status", f"http_{resp.status_code}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for {url}: {e}. Retrying once...")
        time.sleep(5)
        try:
            resp = requests.get(url, headers=headers, timeout=(5, 10))
            resp.raise_for_status()
            data = parse_html_response(resp, url)
            data["access_status"] = data.get("access_status", f"http_{resp.status_code}")
            return data
        except Exception as retry_e:
            error_text = str(retry_e)
            access_status = "http_404" if "404" in error_text else "network_failed"
            return {
                "source": urlparse(url).netloc,
                "url": url,
                "status": "failed",
                "access_status": access_status,
                "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
                "error_type": error_text,
            }
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return {
            "source": urlparse(url).netloc,
            "url": url,
            "status": "failed",
            "access_status": "failed",
            "checked_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
            "error_type": str(e),
        }

def is_transient_collection_failure(data):
    status = data.get("status")
    error_type = data.get("error_type", "")

    if status == "blocked_or_limited":
        return error_type != "robots.txt disallowed"

    if status != "failed":
        return False

    if "404 Client Error" in error_type:
        return False

    return any(marker in error_type for marker in TRANSIENT_ERROR_MARKERS)

def preserve_existing_success(existing_data, attempted_data, url):
    if not isinstance(existing_data, dict):
        return attempted_data

    if existing_data.get("status") != "success":
        return attempted_data

    if existing_data.get("url") != url:
        return attempted_data

    if not is_transient_collection_failure(attempted_data):
        return attempted_data

    logger.warning(
        "Keeping previous successful data for %s after transient collection failure: %s",
        url,
        attempted_data.get("error_type", ""),
    )
    preserved_data = dict(existing_data)
    preserved_data["last_attempt_status"] = attempted_data.get("status", "")
    preserved_data["last_attempt_error_type"] = attempted_data.get("error_type", "")
    preserved_data["last_attempt_at"] = get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST")
    return preserved_data

def is_transient_provider_access_failure(provider_access):
    if not isinstance(provider_access, dict):
        return False
    if provider_access.get("status") == "success":
        return False
    access_status = provider_access.get("access_status", "")
    error_type = provider_access.get("error_type", "")
    status = provider_access.get("status", "")

    if access_status == "robots_disallowed":
        return True
    if status == "blocked_or_limited":
        return True
    if status != "failed":
        return False
    if "404" in error_type:
        return False
    return True

def preserve_existing_provider_success(existing_data, attempted_data):
    if not isinstance(existing_data, dict) or not isinstance(attempted_data, dict):
        return attempted_data

    existing_provider = existing_data.get("machine_data_page", {}).get("provider_access", {})
    attempted_provider = attempted_data.get("machine_data_page", {}).get("provider_access", {})
    if existing_provider.get("status") != "success":
        return attempted_data
    if not is_transient_provider_access_failure(attempted_provider):
        return attempted_data

    preserved_data = dict(attempted_data)
    preserved_page = dict(preserved_data.get("machine_data_page", {}))
    preserved_provider = backfill_provider_access_summary(existing_provider)
    preserved_provider = dict(preserved_provider)
    preserved_provider["last_provider_attempt_status"] = attempted_provider.get("status", "")
    preserved_provider["last_provider_attempt_access_status"] = attempted_provider.get("access_status", "")
    preserved_provider["last_provider_attempt_error_type"] = attempted_provider.get("error_type", "")
    preserved_provider["last_provider_attempt_at"] = get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST")
    preserved_provider["last_provider_parser_version_attempted"] = PROVIDER_PARSER_VERSION
    preserved_page["provider_access"] = preserved_provider
    preserved_data["machine_data_page"] = preserved_page
    return preserved_data

def main():
    stores_data = load_json(get_data_path('stores.json'), {})
    stores = stores_data.get('stores', []) if isinstance(stores_data, dict) else stores_data

    collected_path = get_data_path('collected.json')
    results = load_json(collected_path, {})

    now = get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST")
    urls_processed = 0

    prepare_non_request_entries(results, stores, now)
    tasks = build_collection_tasks(stores, results)
    logger.info("Prepared %s collection tasks. Processing up to %s network requests.", len(tasks), MAX_URLS_PER_RUN)

    for task in tasks:
        if urls_processed >= MAX_URLS_PER_RUN:
            logger.info("Reached maximum URLs per run limit.")
            break

        store = task["store"]
        store_id = store["id"]
        store_result = results[store_id]
        store_result["checked_at"] = now
        made_request = True

        if task["type"] == "link":
            link_type = task["link_type"]
            url = task["url"]
            logger.info("Processing link: %s / %s (%s)", store["name"], link_type, url)

            existing_data = store_result.get("links_data", {}).get(link_type, {})
            data = scrape_url(url)
            data = preserve_existing_success(existing_data, data, url)
            data = preserve_existing_provider_success(existing_data, data)
            store_result["links_data"][link_type] = data
        elif task["type"] == "machine_source":
            source = task["source"]
            key = task["source_key"]
            url = task["url"]
            logger.info("Processing machine-data source: %s / %s (%s)", store["name"], key, url)

            existing_data = store_result.get("machine_data_sources", {}).get(key, {})
            data = find_collected_url_data(store_result.get("links_data", {}), url)
            reused_link_data = data is not None
            made_request = not reused_link_data
            if not reused_link_data:
                data = probe_machine_source(source)
            data = preserve_existing_success(existing_data, data, url)
            data = preserve_existing_provider_success(existing_data, data)
            data["provider"] = source.get("provider", "")
            data["kind"] = source.get("kind", "")
            data["declared_access_status"] = source.get("access_status", "")
            data["notes"] = source.get("notes", "")
            store_result["machine_data_sources"][key] = data
        else:
            logger.warning("Unknown collection task type: %s", task["type"])
            continue

        if made_request:
            urls_processed += 1
            sleep_time = random.uniform(5.0, 10.0)
            logger.info(f"Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    save_json(results, collected_path)
    logger.info("Collection finished.")

if __name__ == "__main__":
    main()
