"""Canonical, deterministic builder for jiggle-zone.zip.

Every release artifact and every packaging test goes through this module, so the
same source tree always produces the same bytes and the same SHA-256.

    python build_zip.py            # rebuild jiggle-zone.zip
    python build_zip.py --check    # rebuild twice, compare, and verify contents

Layout: one top-level `jiggle_zone/` folder holding blender_manifest.toml,
__init__.py, README.md, CHANGELOG.md and assets/. `__pycache__` and compiled
files are excluded. Entry order and timestamps are fixed.
"""

import hashlib
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(ROOT, "jiggle_zone")
ZIP_PATH = os.path.join(ROOT, "jiggle-zone.zip")
ARCHIVE_ROOT = "jiggle_zone"
STAMP = (2026, 11, 14, 0, 0, 0)
SKIP_SUFFIXES = (".pyc", ".pyo", ".blend1")

EXPECTED_ENTRIES = (
    "jiggle_zone/CHANGELOG.md",
    "jiggle_zone/README.md",
    "jiggle_zone/__init__.py",
    "jiggle_zone/assets/BackFaces.blend",
    "jiggle_zone/assets/JiggleV2.blend",
    "jiggle_zone/assets/Wiggy_0.1.blend",
    "jiggle_zone/assets/Wiggy_0.2.0.blend",
    "jiggle_zone/blender_manifest.toml",
)


def collect(addon_dir=ADDON_DIR):
    """Return [(archive_name, source_path)] sorted by archive name."""
    entries = []
    for base, dirs, files in os.walk(addon_dir):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            if name.endswith(SKIP_SUFFIXES):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, addon_dir).replace("\\", "/")
            entries.append((f"{ARCHIVE_ROOT}/{rel}", path))
    return sorted(entries)


def build(out_path=ZIP_PATH, addon_dir=ADDON_DIR, stamp=STAMP):
    """Write the archive and return (path, entries)."""
    entries = collect(addon_dir)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for archive_name, source in entries:
            info = zipfile.ZipInfo(archive_name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(source, "rb") as handle:
                archive.writestr(info, handle.read())
    return out_path, entries


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def verify(zip_path=ZIP_PATH, addon_dir=ADDON_DIR):
    """Return a list of problems; empty means the archive is release-ready."""
    problems = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        corrupt = archive.testzip()
        if corrupt is not None:
            problems.append(f"corrupt entry {corrupt}")
        for name in names:
            if "\\" in name:
                problems.append(f"backslash in entry {name}")
            if "__pycache__" in name or name.endswith(SKIP_SUFFIXES):
                problems.append(f"unwanted entry {name}")
        if sorted(names) != sorted(EXPECTED_ENTRIES):
            problems.append(f"unexpected entry set {sorted(names)}")
        packaged = archive.read(f"{ARCHIVE_ROOT}/__init__.py")
    with open(os.path.join(addon_dir, "__init__.py"), "rb") as handle:
        source = handle.read()
    if hashlib.sha256(packaged).digest() != hashlib.sha256(source).digest():
        problems.append("packaged __init__.py differs from the source tree")
    return problems


def check(addon_dir=ADDON_DIR):
    """Build twice and confirm the bytes are identical. Returns the SHA-256."""
    first, _ = build(ZIP_PATH, addon_dir)
    first_hash = sha256_file(first)
    with open(first, "rb") as handle:
        first_bytes = handle.read()
    second, _ = build(ZIP_PATH, addon_dir)
    second_bytes = open(second, "rb").read()
    if first_bytes != second_bytes:
        raise SystemExit("FAIL rebuild is not byte-identical")
    problems = verify(second, addon_dir)
    if problems:
        for problem in problems:
            print("FAIL", problem)
        raise SystemExit(1)
    return second_bytes, first_hash


def main(argv):
    if "--check" in argv:
        blob, digest = check()
        print("entries:", len(EXPECTED_ENTRIES))
        print("zip bytes:", len(blob))
        print("zip sha256:", digest)
        print("PASS deterministic rebuild verified")
        return 0
    path, entries = build()
    print("entries:", len(entries))
    for archive_name, _ in entries:
        print("  ", archive_name)
    print("zip bytes:", os.path.getsize(path))
    print("zip sha256:", sha256_file(path))
    problems = verify(path)
    if problems:
        for problem in problems:
            print("FAIL", problem)
        return 1
    print("PASS", os.path.basename(path), "built and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
