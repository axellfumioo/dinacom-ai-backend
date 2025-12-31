import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.services.search.cache import TTLCache

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

GOOGLE_SEARCH_COUNT = os.getenv("GOOGLE_SEARCH_COUNT")

_GOOGLE_TIMEOUT_S = float(os.getenv("GOOGLE_SEARCH_TIMEOUT_S", "5"))


_GOOGLE_CACHE_TTL_S = int(os.getenv("GOOGLE_SEARCH_CACHE_TTL_S", "300"))
_google_cache = TTLCache(ttl=_GOOGLE_CACHE_TTL_S)

_CONNECT_TIMEOUT_S = float(os.getenv("GOOGLE_SEARCH_CONNECT_TIMEOUT_S", "1"))
_READ_TIMEOUT_S = float(os.getenv("GOOGLE_SEARCH_READ_TIMEOUT_S", str(_GOOGLE_TIMEOUT_S)))

_RETRY_TOTAL = int(os.getenv("GOOGLE_SEARCH_RETRY_TOTAL", "1"))
_RETRY_BACKOFF = float(os.getenv("GOOGLE_SEARCH_RETRY_BACKOFF", "0.2"))

_session = requests.Session()
_retries = Retry(
    total=max(0, _RETRY_TOTAL),
    connect=max(0, _RETRY_TOTAL),
    read=max(0, _RETRY_TOTAL),
    status=max(0, _RETRY_TOTAL),
    backoff_factor=max(0.0, _RETRY_BACKOFF),
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET"]),
    raise_on_status=False,
    respect_retry_after_header=True,
)
_adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=_retries)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


_proxy = os.getenv("SEARCH_PROXY")
_http_proxy = os.getenv("SEARCH_HTTP_PROXY") or _proxy
_https_proxy = os.getenv("SEARCH_HTTPS_PROXY") or _proxy
if _http_proxy or _https_proxy:
    _session.proxies.update({k: v for k, v in {"http": _http_proxy, "https": _https_proxy}.items() if v})


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default

def google_search(query: str, num_results: int = None) -> list[str]:
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise RuntimeError("Missing GOOGLE_API_KEY / GOOGLE_CSE_ID env vars")

    if num_results is None:
        num_results = _to_int(GOOGLE_SEARCH_COUNT, 5)

    
    num_results = max(1, min(10, int(num_results)))

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results,
    }

    cache_key = f"q={query}\nnum={num_results}"
    cached = _google_cache.get(cache_key)
    if cached:
        return cached

    res = _session.get(
        url,
        params=params,
        timeout=(_CONNECT_TIMEOUT_S, _READ_TIMEOUT_S),
        headers={"Accept": "application/json"},
    )
    res.raise_for_status()

    data = res.json()
    items = data.get("items", [])

    links = [item.get("link") for item in items if item.get("link")]
    _google_cache.set(cache_key, links)
    return links
