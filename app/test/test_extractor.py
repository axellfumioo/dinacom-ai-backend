import os
import sys

sys.path.append(os.path.abspath("."))

from app.services.search.extractor import extract_web_content


def main() -> None:
	response = extract_web_content(
		"https://www.kompas.id/artikel/pengamen-dan-sisi-lain-pertumbuhan-kota?open_from=Artikel_Opini_Page"
	)
	print(response)


if __name__ == "__main__":
	main()
