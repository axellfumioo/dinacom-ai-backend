import requests
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

GOOGLE_SEARCH_COUNT = os.getenv("GOOGLE_SEARCH_COUNT")

def google_search(query: str, num_results: int = GOOGLE_SEARCH_COUNT) -> list[str]:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results,
    }

    res = requests.get(url, params=params, timeout=10)
    res.raise_for_status()

    data = res.json()
    items = data.get("items", [])

    return [item["link"] for item in items]
