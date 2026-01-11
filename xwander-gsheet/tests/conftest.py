"""Pytest configuration for xwander-gsheet tests"""
import pytest
import os
import sys

# Add plugin directory to path for imports
plugin_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if plugin_path not in sys.path:
    sys.path.insert(0, plugin_path)
