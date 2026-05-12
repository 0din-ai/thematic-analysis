"""PyInstaller entry point for the thematic-analysis app.

This thin bootstrap script:
1. Sets TIKTOKEN_CACHE_DIR to the bundled cache before any imports
   touch tiktoken (tiktoken reads it on first import).
2. Calls the Flask app's main() function.

We need a separate entry script because app.py uses relative imports
(from .config import ...) that only work inside a package, not as a
top-level PyInstaller entry point.
"""

import os
import sys

# Point tiktoken at the bundled cache directory so it never downloads
if getattr(sys, "frozen", False):
    _cache = os.path.join(sys._MEIPASS, "tiktoken_cache")
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", _cache)

from thematic_analysis.app import main  # noqa: E402

if __name__ == "__main__":
    main()
