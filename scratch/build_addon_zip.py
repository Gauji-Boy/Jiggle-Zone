"""Rebuild jiggle-zone.zip from jiggle_zone/ with deterministic timestamps.

Layout matches the previous release: one top-level `jiggle_zone/` folder holding
blender_manifest.toml, __init__.py, README.md, CHANGELOG.md and assets/.
__pycache__ is excluded. Entry order and timestamps are fixed, so the same source
always produces the same bytes and the same SHA-256.
"""
import hashlib
import os
import zipfile

SRC = r"D:\Blender\Giggle\jiggle_zone"
OUT = r"D:\Blender\Giggle\jiggle-zone.zip"
STAMP = (2026, 11, 14, 0, 0, 0)

files = []
for root, dirs, names in os.walk(SRC):
    dirs[:] = sorted(d for d in dirs if d != "__pycache__")
    for name in sorted(names):
        if name.endswith((".pyc", ".pyo")) or name.endswith(".blend1"):
            continue
        path = os.path.join(root, name)
        rel = os.path.relpath(path, os.path.dirname(SRC)).replace("\\", "/")
        files.append((rel, path))
files.sort()

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for rel, path in files:
        info = zipfile.ZipInfo(rel, date_time=STAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        with open(path, "rb") as fh:
            zf.writestr(info, fh.read())

size = os.path.getsize(OUT)
digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print("entries:", len(files))
for rel, _ in files:
    print("  ", rel)
print("zip bytes:", size)
print("zip sha256:", digest)

# Verify the archive reads back and the add-on source inside it matches the tree.
with zipfile.ZipFile(OUT) as zf:
    bad = zf.testzip()
    print("testzip:", "ok" if bad is None else "corrupt: %s" % bad)
    inside = zf.read("jiggle_zone/__init__.py")
src = open(os.path.join(SRC, "__init__.py"), "rb").read()
print("embedded __init__.py matches tree:", inside == src)
