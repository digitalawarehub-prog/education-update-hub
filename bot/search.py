"""Compatibility search module for Education Update Hub.
Delegates search operations to the production Search V5 engine.
"""
from search_engine import (
    load_index,
    search,
    search_category,
    search_department,
)

__all__ = ["load_index", "search", "search_category", "search_department"]
