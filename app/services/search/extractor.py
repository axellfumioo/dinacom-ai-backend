import os
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_EXTRACT_TIMEOUT_S = float(os.getenv("SEARCH_EXTRACT_TIMEOUT_S", "6"))
_CONNECT_TIMEOUT_S = float(os.getenv("SEARCH_EXTRACT_CONNECT_TIMEOUT_S", "1"))
_READ_TIMEOUT_S = float(os.getenv("SEARCH_EXTRACT_READ_TIMEOUT_S", "2.5"))

_MAX_BYTES = int(os.getenv("SEARCH_EXTRACT_MAX_BYTES", "400000"))

_RETRY_TOTAL = int(os.getenv("SEARCH_EXTRACT_RETRY_TOTAL", "0"))
_RETRY_BACKOFF = float(os.getenv("SEARCH_EXTRACT_RETRY_BACKOFF", "0.2"))

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


def _download_html(url: str) -> str:
    
    timeout = (_CONNECT_TIMEOUT_S, _READ_TIMEOUT_S)
    if _EXTRACT_TIMEOUT_S > 0 and _EXTRACT_TIMEOUT_S < (_CONNECT_TIMEOUT_S + _READ_TIMEOUT_S):
        timeout = _EXTRACT_TIMEOUT_S

    res = _session.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        stream=True,
    )
    res.raise_for_status()

    chunks: list[bytes] = []
    total = 0
    for chunk in res.iter_content(chunk_size=65536):
        if not chunk:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total >= _MAX_BYTES:
            break

    raw = b"".join(chunks)
    encoding = res.encoding or "utf-8"
    return raw.decode(encoding, errors="ignore")

def extract_web_content(url: str) -> str:
    try:
        html = _download_html(url)
        
        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "iframe"]):
            tag.decompose()
            
        text = soup.get_text(separator=" ")
        return " ".join(text.split())

    except Exception as e:
        return f"[ERROR extracting {url}] {str(e)}"
