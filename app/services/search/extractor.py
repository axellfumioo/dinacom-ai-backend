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

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside" "iframe", "hero"]):
            tag.decompose()
            
        for tag in soup.find_all(attrs={"class": lambda x: x and any(keyword in x for keyword in ["google-map", "map-container", "location-map", "link"])}):
            tag.decompose()

        for tag in soup.find_all(string=lambda text: text and any(keyword in text.lower() for keyword in ["phone", "contact", "tel", "call", "link"])):
            tag.extract()
            
        text = soup.get_text(separator=" ")
        return " ".join(text.split())

    except Exception as e:
        return f"[ERROR extracting {url}] {str(e)}"
