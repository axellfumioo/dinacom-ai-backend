"""Smoke test: extract readable text from a PDF URL."""

from __future__ import annotations


def main() -> None:
    from app.services.search.extractor import extract_web_content

    url = "https://kemkes.go.id/app_asset/file_content_download/172231123666a86244b83fd8.51637104.pdf"
    text = extract_web_content(url)
    print(text[:1200])
    print("\n---\nlen=", len(text))


if __name__ == "__main__":
    main()
