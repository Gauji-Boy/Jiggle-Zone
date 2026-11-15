"""Deprecated shim. The canonical builder is `build_zip.py` at the repo root.

Kept so existing notes that call `scratch/build_addon_zip.py` still work, without
maintaining a second implementation that could drift.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_zip  # noqa: E402

if __name__ == "__main__":
    sys.exit(build_zip.main(sys.argv[1:]))
