import shutil
import zipfile
import os

src = r'd:\Blender\Giggle\giggle_addon\__init__.py'
dests = [
    r'C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.3\extensions\user_default\giggle_physics\__init__.py',
    r'C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\giggle_physics\__init__.py',
    r'C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\giggle_addon\__init__.py'
]

for d in dests:
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(src, d)
    print(f"Copied to {d}")

# Repack giggle_addon.zip
zip_path = r'D:\Blender\Giggle\giggle_addon.zip'
base_dir = r'D:\Blender\Giggle'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(os.path.join(base_dir, 'giggle_addon')):
        for file in files:
            full_path = os.path.join(root, file)
            arcname = os.path.relpath(full_path, base_dir)
            zf.write(full_path, arcname)

print(f"Repacked {zip_path} successfully!")
