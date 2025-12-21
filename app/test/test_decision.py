from dotenv import load_dotenv
load_dotenv()

from app.ai.decision import DecisionService

decision = DecisionService()

tests = [
    "harga emas hari ini",
    "harga bitcoin sekarang",
    "jelasin apa itu clean architecture"
]

for t in tests:
    print("\nUSER:", t)
    print("DECISION:", decision.run(t))
