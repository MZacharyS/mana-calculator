"""
Pytest configuration — adds the project root to sys.path so that
`from src.engine.tiers import ...` works without installing the package.
"""
import sys
import os

# Insert the mana-calculator root (parent of this tests/ directory)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
