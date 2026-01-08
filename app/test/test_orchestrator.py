import os
import sys

sys.path.append(os.path.abspath("."))

from app.ai.orchestrator import Orchestrator


def main() -> None:
	orch = Orchestrator()
	response = orch.handle_chat("sakit pinggang solusi nya apa ya")
	print(response)


if __name__ == "__main__":
	main()
