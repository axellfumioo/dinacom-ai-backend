# app/test/test_orchestrator.py
import sys
import os

sys.path.append(os.path.abspath("."))

from app.services.search.extractor import extract_web_content

response = extract_web_content("https://www.kompas.id/artikel/pengamen-dan-sisi-lain-pertumbuhan-kota?open_from=Artikel_Opini_Page")
print(response)
