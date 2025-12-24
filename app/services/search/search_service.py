from app.services.search.cache import TTLCache
from app.services.search.google_search import google_search
from app.services.search.extractor import extract_web_content

cache = TTLCache(ttl=300)

def search_and_extract(query: str):
    cached = cache.get(query)
    if cached:
        return cached

    urls = google_search(query)
    contents = []

    for url in urls:
        text = extract_web_content(url)
        contents.append({
            "url": url,
            "content": text[:5000]
        })

    result = {
        "query": query,
        "results": contents
    }

    cache.set(query, result)
    return result
