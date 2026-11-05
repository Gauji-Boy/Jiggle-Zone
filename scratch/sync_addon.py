import shutil
import os

src = r"d:\Blender\Giggle\giggle_addon\__init__.py"
destinations = [
    r"C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.3\extensions\user_default\giggle_physics\__init__.py",
    r"C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\giggle_physics\__init__.py",
    r"C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\giggle_addon\__init__.py",
]

for dst in destinations:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Synced to: {dst}")

print("All destination directories synced successfully.")
