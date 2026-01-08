import os
import sys

sys.path.append(os.path.abspath("."))

from app.services.search.search_service import search_and_extract


def main() -> None:
	response = search_and_extract("Gejala Batuk apa aja si?")
	print(response)


if __name__ == "__main__":
	main()
