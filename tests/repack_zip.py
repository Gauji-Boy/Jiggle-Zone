"""Verify jiggle-zone.zip against the source tree.

    blender -b --factory-startup --python-exit-code 1 --python tests/repack_zip.py

Every check here runs through `build_zip.py`, the canonical builder, so this test
cannot produce an archive that differs from the release artifact.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_zip  # noqa: E402


def main():
    blob, digest = build_zip.check()
    print("entries :", len(build_zip.EXPECTED_ENTRIES))
    print("zip size:", len(blob), "bytes")
    print("zip sha :", digest.upper())
    print("PASS deterministic rebuild, contents and embedded source verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
