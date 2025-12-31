from pathlib import Path
from functools import lru_cache

ROOT_PROMPT_DIR = Path(__file__).parent

@lru_cache(maxsize=32)
def load_prompt(filename: str) -> str:
    path = ROOT_PROMPT_DIR / filename
    
    if not path.exists():
        raise FileNotFoundError(f"Root Prompt not found {filename}")
    
    return path.read_text(encoding="utf-8")