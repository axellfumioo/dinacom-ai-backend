from pathlib import Path

ROOT_PROMPT_DIR = Path(__file__).parent

def load_prompt(filename: str) -> str:
    path = ROOT_PROMPT_DIR / filename
    
    if not path.exists():
        raise FileNotFoundError(f"Root Prompt not found {filename}")
    
    return path.read_text()