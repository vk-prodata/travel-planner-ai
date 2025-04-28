import os
import sys
import pytest
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Configure event loop policy for async tests
@pytest.fixture(scope="session")
def event_loop_policy():
    """Return an event loop policy for async tests."""
    return asyncio.DefaultEventLoopPolicy() 