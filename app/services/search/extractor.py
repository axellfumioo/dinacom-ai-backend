import requests
from bs4 import BeautifulSoup

def extract_web_content(url: str) -> str:
    try:
        res = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # buang noise
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        return " ".join(text.split())

    except Exception as e:
        return f"[ERROR extracting {url}] {str(e)}"
