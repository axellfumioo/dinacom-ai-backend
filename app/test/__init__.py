"""
Package marker for tests so test modules can be run with -m (e.g. python -m app.test.test_decision)

Keeping tests as a proper subpackage avoids ModuleNotFoundError when executing modules from the project root.
"""

__all__ = []
from dotenv import load_dotenv

load_dotenv()

