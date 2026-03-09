import pytest
from app import main


def test_main_function_exists():
    """Verify that main() entry point is importable and callable."""
    assert callable(main.main)
