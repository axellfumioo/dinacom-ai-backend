import os
import requests
import io
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_EXTRACT_TIMEOUT_S = float(os.getenv("SEARCH_EXTRACT_TIMEOUT_S", "6"))
_CONNECT_TIMEOUT_S = float(os.getenv("SEARCH_EXTRACT_CONNECT_TIMEOUT_S", "1"))
_READ_TIMEOUT_S = float(os.getenv("SEARCH_EXTRACT_READ_TIMEOUT_S", "2.5"))

_MAX_BYTES = int(os.getenv("SEARCH_EXTRACT_MAX_BYTES", "2000000"))

_RETRY_TOTAL = int(os.getenv("SEARCH_EXTRACT_RETRY_TOTAL", "1"))
_RETRY_BACKOFF = float(os.getenv("SEARCH_EXTRACT_RETRY_BACKOFF", "0.2"))

_PREFERRED_PARSER = os.getenv("SEARCH_EXTRACT_BS_PARSER", "lxml").strip() or "lxml"
_PDF_MAX_PAGES = int(os.getenv("SEARCH_EXTRACT_PDF_MAX_PAGES", "12"))

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


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
    }


def _compute_timeout():
    timeout = (_CONNECT_TIMEOUT_S, _READ_TIMEOUT_S)
    if _EXTRACT_TIMEOUT_S > 0 and _EXTRACT_TIMEOUT_S < (_CONNECT_TIMEOUT_S + _READ_TIMEOUT_S):
        timeout = _EXTRACT_TIMEOUT_S
    return timeout


def _download_bytes(url: str) -> tuple[bytes, str]:
    res = _session.get(
        url,
        timeout=_compute_timeout(),
        headers=_default_headers(),
        stream=True,
    )

    if res.status_code >= 400:
        reason = (res.reason or "").strip()
        extra = f" {reason}" if reason else ""
        raise requests.HTTPError(f"HTTP {res.status_code}{extra}")

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
    content_type = (res.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    return raw, content_type


def _download_html(url: str) -> str:
    
    raw, _ = _download_bytes(url)
    return raw.decode("utf-8", errors="ignore")


def _is_probably_pdf(url: str, content_type: str, raw: bytes) -> bool:
    if content_type == "application/pdf":
        return True
    if url.lower().split("?", 1)[0].endswith(".pdf"):
        return True
    return raw[:5] == b"%PDF-"


def _extract_pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as e:  
        raise RuntimeError("Missing dependency: pypdf") from e

    reader = PdfReader(io.BytesIO(raw))
    texts: list[str] = []
    max_pages = max(1, _PDF_MAX_PAGES)
    for i, page in enumerate(reader.pages[:max_pages]):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t:
            texts.append(t)

    text = "\n".join(texts)
    text = " ".join(text.split())
    if not text:
        raise ValueError("PDF has no extractable text")
    return text

def extract_web_content(url: str) -> str:
    try:
        raw, content_type = _download_bytes(url)

        if _is_probably_pdf(url, content_type, raw):
            return _extract_pdf_text(raw)

        html = raw.decode("utf-8", errors="ignore")

        try:
            soup = BeautifulSoup(html, _PREFERRED_PARSER)
        except FeatureNotFound:
            soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "iframe"]):
            tag.decompose()
            
        text = soup.get_text(separator=" ")
        return " ".join(text.split())

    except Exception as e:
        msg = str(e).strip() or e.__class__.__name__
        return f"[ERROR extracting {url}] {msg}"
