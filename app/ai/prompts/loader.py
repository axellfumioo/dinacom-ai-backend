from pathlib import Path
from functools import lru_cache

PROMPT_DIR = Path(__file__).parent

@lru_cache(maxsize=64)
def load_prompt(filename: str) -> str:
    path = PROMPT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {filename}")
    
    return path.read_text(encoding="utf-8")