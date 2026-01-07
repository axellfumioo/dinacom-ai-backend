import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.services.search.cache import TTLCache


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

GOOGLE_SEARCH_COUNT = int(os.getenv("GOOGLE_SEARCH_COUNT", "5"))
GOOGLE_TIMEOUT_S = float(os.getenv("GOOGLE_SEARCH_TIMEOUT_S", "5"))
GOOGLE_CACHE_TTL_S = int(os.getenv("GOOGLE_SEARCH_CACHE_TTL_S", "300"))

CONNECT_TIMEOUT_S = float(os.getenv("GOOGLE_SEARCH_CONNECT_TIMEOUT_S", "1"))
READ_TIMEOUT_S = float(os.getenv("GOOGLE_SEARCH_READ_TIMEOUT_S", str(GOOGLE_TIMEOUT_S)))

RETRY_TOTAL = int(os.getenv("GOOGLE_SEARCH_RETRY_TOTAL", "1"))
RETRY_BACKOFF = float(os.getenv("GOOGLE_SEARCH_RETRY_BACKOFF", "0.2"))


if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    raise RuntimeError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID")


google_cache = TTLCache(ttl=GOOGLE_CACHE_TTL_S)


session = requests.Session()

retries = Retry(
    total=max(0, RETRY_TOTAL),
    connect=max(0, RETRY_TOTAL),
    read=max(0, RETRY_TOTAL),
    status=max(0, RETRY_TOTAL),
    backoff_factor=max(0.0, RETRY_BACKOFF),
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET"]),
    raise_on_status=False,
    respect_retry_after_header=True,
)

adapter = HTTPAdapter(
    pool_connections=20,
    pool_maxsize=20,
    max_retries=retries,
)

session.mount("http://", adapter)
session.mount("https://", adapter)


proxy = os.getenv("SEARCH_PROXY")
http_proxy = os.getenv("SEARCH_HTTP_PROXY") or proxy
https_proxy = os.getenv("SEARCH_HTTPS_PROXY") or proxy

if http_proxy or https_proxy:
    session.proxies.update(
        {k: v for k, v in {"http": http_proxy, "https": https_proxy}.items() if v}
    )


def google_search(query: str, num_results: int | None = None) -> list[str]:
    num = num_results or GOOGLE_SEARCH_COUNT
    num = max(1, min(10, int(num)))

    cache_key = f"{query}:{num}"
    cached = google_cache.get(cache_key)
    if cached:
        return cached

    res = session.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "num": num,
        },
        timeout=(CONNECT_TIMEOUT_S, READ_TIMEOUT_S),
        headers={"Accept": "application/json"},
    )

    res.raise_for_status()
    data = res.json()

    links = [item["link"] for item in data.get("items", []) if "link" in item]

    google_cache.set(cache_key, links)
    return links
