"""
Ensures the project root is importable as `chatbot` regardless of the
directory pytest is invoked from, without requiring an editable install.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
