"""Make the scraper package importable as top-level modules in tests."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
