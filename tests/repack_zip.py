"""Rebuild giggle_addon.zip from the source tree and verify its contents.

    blender -b --factory-startup --python-exit-code 1 --python tests/repack_zip.py

The zip root is `giggle_addon/`, paths use forward slashes, and no `__pycache__` or `.pyc`
is included. The packaged entry must hash the same as the source file.
"""

import hashlib
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(ROOT, "giggle_addon")
ZIP = os.path.join(ROOT, "giggle_addon.zip")
SOURCE = os.path.join(ADDON, "__init__.py")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest().upper()


def build():
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for base, dirs, files in os.walk(ADDON):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(files):
                if name.endswith((".pyc", ".pyo")):
                    continue
                full = os.path.join(base, name)
                arc = "giggle_addon/" + os.path.relpath(full, ADDON).replace("\\", "/")
                archive.write(full, arc)
                print("added", arc)


def verify():
    failures = []
    with zipfile.ZipFile(ZIP) as archive:
        names = archive.namelist()
        for name in names:
            if "__pycache__" in name or name.endswith((".pyc", ".pyo")):
                failures.append(f"unwanted entry {name}")
            if "\\" in name:
                failures.append(f"backslash in entry {name}")
        entry = archive.read("giggle_addon/__init__.py")
    with open(SOURCE, "rb") as handle:
        source = handle.read()
    if sha256_bytes(entry) != sha256_bytes(source):
        failures.append("packaged __init__.py differs from the source tree")
    print("entries:", names)
    print("entry  :", sha256_bytes(entry))
    print("source :", sha256_bytes(source))
    return failures


if __name__ == "__main__":
    build()
    problems = verify()
    print("zip size:", os.path.getsize(ZIP), "bytes")
    print("zip sha :", sha256_bytes(open(ZIP, "rb").read()))
    if problems:
        for problem in problems:
            print("FAIL", problem)
        sys.exit(1)
    print("PASS zip rebuilt and verified")
