"""Offline smoke tests for search/extract plumbing.

This module is intentionally executable as a script and avoids network calls.
"""

from __future__ import annotations


def main() -> None:
    from app.services.search import search_service

    # Monkeypatch search to avoid network.
    search_service.google_search = lambda q: [
        "https://example.com/a",
        "https://example.com/a",  # dup
        "https://example.com/b",
    ]

    # Monkeypatch extractor to avoid network.
    search_service.extract_web_content = lambda url: ("x" * 400) + " " + url
    search_service._get_cached_or_extract = lambda url: search_service.extract_web_content(url)

    res = search_service.search_and_extract("dummy query")
    assert res["results"], "no results"
    assert len({r["url"] for r in res["results"]}) == len(res["results"]), "duplicate URLs in results"

    print("OK")


if __name__ == "__main__":
    main()
