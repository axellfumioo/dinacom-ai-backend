from dotenv import load_dotenv
load_dotenv()

from app.ai.decision import DecisionService
import time

decision = DecisionService()

test = "apa gejala covid?"

start_time = time.time()
result = decision.run(test)
end_time = time.time()
elapsed_time = (end_time - start_time) * 1000
print("\nUSER:", test)
print("DECISION:", result)
print(f"Processing time: {elapsed_time:.2f} ms")