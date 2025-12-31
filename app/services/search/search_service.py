from app.services.search.cache import TTLCache
from app.services.search.google_search import google_search
from app.services.search.extractor import extract_web_content
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
from typing import Optional

query_cache = TTLCache(ttl=300)

url_cache = TTLCache(ttl=60 * 60 * 6)

url_error_cache = TTLCache(ttl=int(os.getenv("SEARCH_URL_ERROR_CACHE_TTL_S", "60")))

_MAX_URLS_PER_QUERY = int(os.getenv("SEARCH_MAX_URLS_PER_QUERY", "3"))
_EXTRACT_WORKERS = int(os.getenv("SEARCH_EXTRACT_WORKERS", "6"))
_SEARCH_TOTAL_BUDGET_S = float(os.getenv("SEARCH_TOTAL_BUDGET_S", "3"))


def _is_usable_content(text: str) -> bool:
    if not text:
        return False
    if text.startswith("[ERROR extracting"):
        return False
    return len(text) >= 256


def _get_cached_or_extract(url: str) -> str:
    cached_error = url_error_cache.get(url)
    if cached_error:
        return cached_error
    cached = url_cache.get(url)
    if cached:
        return cached
    text = extract_web_content(url)
    if text and text.startswith("[ERROR extracting"):
        url_error_cache.set(url, text)
    else:
        url_cache.set(url, text)
    return text

def search_and_extract(query: str):
    cached = query_cache.get(query)
    if cached:
        return cached

    urls = google_search(query)
    urls = urls[: max(1, min(_MAX_URLS_PER_QUERY, len(urls)))]

    contents = []
    best: Optional[dict] = None
    
    
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=min(_EXTRACT_WORKERS, max(1, len(urls)))) as executor:
        future_to_url = {executor.submit(_get_cached_or_extract, url): url for url in urls}

        budget_s = max(0.25, _SEARCH_TOTAL_BUDGET_S)
        timeout_s = max(0.0, budget_s - (time.perf_counter() - t0))
        try:
            iterator = as_completed(future_to_url, timeout=timeout_s)
        except TypeError:
            
            iterator = as_completed(future_to_url)

        try:
            for future in iterator:
                if (time.perf_counter() - t0) > budget_s:
                    break

                url = future_to_url[future]
                try:
                    text = future.result()
                except Exception as exc:
                    print(f"URL {url} generated an exception: {exc}")
                    text = "[ERROR extracting] exception"

                item = {"url": url, "content": (text or "")[:3000]}
                contents.append(item)

                if best is None and _is_usable_content(text or ""):
                    best = item
                    break
        except Exception:
            
            pass

        
        for f in future_to_url:
            if not f.done():
                f.cancel()
            url = future_to_url[future]
            try:
                text = future.result()
            except Exception as exc:
                print(f"URL {url} generated an exception: {exc}")
                text = "[ERROR extracting] exception"

            item = {"url": url, "content": (text or "")[:3000]}
            contents.append(item)

            if best is None and _is_usable_content(text or ""):
                best = item
                
                for f in future_to_url:
                    if f is not future:
                        f.cancel()
                break

    if best is not None:
        contents = [best]

    result = {
        "query": query,
        "results": contents
    }

    query_cache.set(query, result)
    return result
