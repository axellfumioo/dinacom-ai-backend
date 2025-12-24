# app/test/test_orchestrator.py
import sys
import os

sys.path.append(os.path.abspath("."))

from app.ai.orchestrator import Orchestrator

orch = Orchestrator()

response = orch.handle_chat("harga emas hari ini")
print(response)
