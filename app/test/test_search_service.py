# app/test/test_orchestrator.py
import sys
import os

sys.path.append(os.path.abspath("."))

from app.services.search.search_service import search_and_extract

response = search_and_extract("Gejala Batuk apa aja si?")
print(response)
