"""Install the packaged ZIP into a clean-ish profile and verify the installed code.

    blender -b --factory-startup --python-exit-code 1 --python tests/runtime/test_clean_install_zip.py

Exits non-zero when the install fails or the installed entry does not match the source.
"""

import hashlib
import os
import re
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = os.path.join(ROOT, "jiggle-zone.zip")
SOURCE = os.path.join(ROOT, "jiggle_zone", "__init__.py")
MANIFEST = os.path.join(ROOT, "jiggle_zone", "blender_manifest.toml")


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest().upper()


def manifest_version():
    with open(MANIFEST, encoding="utf-8") as handle:
        for line in handle:
            if line.strip().startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def read_version_file(path):
    """Version from a manifest, or the bl_info tuple from a module."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if path.endswith("blender_manifest.toml"):
        for line in text.splitlines():
            if line.strip().startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
        return None
    match = re.search(r'"version"\s*:\s*\((\d+),\s*(\d+),\s*(\d+)\)', text)
    return ".".join(match.groups()) if match else None


def main():
    print("BLENDER", bpy.app.version_string)
    assert os.path.exists(ZIP), f"missing package: {ZIP}"
    expected = sha256(SOURCE)
    version = manifest_version()
    print("SOURCE", expected, "MANIFEST", version)

    result = bpy.ops.extensions.package_install_files(
        filepath=ZIP, repo="user_default", enable_on_install=True)
    print("INSTALL", result)
    if result != {'FINISHED'}:
        print("FAIL install returned", result)
        return 1

    installed_dir = os.path.join(bpy.utils.user_resource('EXTENSIONS'),
                                 "user_default", "jiggle_zone")
    installed = os.path.join(installed_dir, "__init__.py")
    if not os.path.exists(installed):
        print("FAIL installed file missing:", installed)
        return 1
    actual = sha256(installed)
    print("INSTALLED", actual)
    if actual != expected:
        print("FAIL installed code differs from source")
        return 1

    # Version must agree in every place that reports one.
    installed_manifest = read_version_file(os.path.join(installed_dir, "blender_manifest.toml"))
    installed_bl_info = read_version_file(installed)
    source_bl_info = read_version_file(SOURCE)
    print("versions: manifest", installed_manifest, "| bl_info", installed_bl_info,
          "| source bl_info", source_bl_info)
    for label, value in (("installed manifest", installed_manifest),
                         ("installed bl_info", installed_bl_info),
                         ("source bl_info", source_bl_info)):
        if value is None:
            print(f"FAIL {label} has no version")
            return 1
        if version and value != version:
            print(f"FAIL {label} is {value}, manifest says {version}")
            return 1

    # And the add-on must actually be live, not just on disk.
    if not hasattr(bpy.ops.jiggle, "bake_all_cages"):
        print("FAIL jiggle operators are not registered after install")
        return 1

    print("PASS clean install matches the source tree and reports version", version)
    return 0


sys.exit(main())
