import os

INIT_PATH = r"d:\Blender\Giggle\giggle_addon\__init__.py"

with open(INIT_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add hashlib and time to top imports if missing
top_import_target = "import json\nimport re"
top_import_replacement = "import json\nimport re\nimport hashlib\nimport shutil\nimport time"
assert top_import_target in content, "Top import target not found"
content = content.replace(top_import_target, top_import_replacement, 1)

# 2. Add check_cache_on_render to GiggleSceneSettings
setting_target = """    bake_disk_path: StringProperty(
        name="Bake Directory",
        description="Directory for external cache files",
        subtype='DIR_PATH',
        default="//giggle_cache/"
    )"""

setting_replacement = """    bake_disk_path: StringProperty(
        name="Bake Directory",
        description="Directory for external cache files",
        subtype='DIR_PATH',
        default="//giggle_cache/"
    )
    check_cache_on_render: BoolProperty(
        name="Pre-Flight Render Check",
        description="Verify simulation caches match current animation and physics before rendering",
        default=True
    )"""
assert setting_target in content, "Setting target not found"
content = content.replace(setting_target, setting_replacement, 1)

print("Imports and scene settings updated.")
