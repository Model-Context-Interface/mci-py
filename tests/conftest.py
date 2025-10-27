"""
Pytest configuration for tests.

Configure anyio to use only asyncio backend (not trio).
"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio to use only asyncio backend."""
    return "asyncio"
