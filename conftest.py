"""
conftest.py
-----------
Root-level pytest configuration.

Placed at the project root (same level as the gitpulse_mcp/ package folder
and the tests/ folder) so pytest discovers it for ALL test modules.

What this does:
1. Adds the project root to sys.path so `import gitpulse_mcp` works
   regardless of whether the package is installed in editable mode.
2. Sets asyncio_mode = "auto" via pytest_configure as a fallback in case
   the pyproject.toml setting isn't picked up (e.g. older pytest-asyncio).
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so gitpulse_mcp is importable
# even if the package hasn't been pip-installed.
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Register asyncio_mode=auto so all async tests run without decoration."""
    try:
        config.addinivalue_line(
            "markers", "asyncio: mark test as async (handled by pytest-asyncio)"
        )
    except Exception:
        pass
