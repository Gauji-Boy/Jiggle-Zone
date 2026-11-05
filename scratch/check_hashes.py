import hashlib

def get_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

f1 = r'd:\Blender\Giggle\giggle_addon\__init__.py'
f2 = r'C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.3\extensions\user_default\giggle_physics\__init__.py'
f3 = r'C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\giggle_physics\__init__.py'
f4 = r'C:\Users\susha\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\giggle_addon\__init__.py'

h1 = get_hash(f1)
print(f"Source: {h1[:16]}")
for p in [f2, f3, f4]:
    try:
        hp = get_hash(p)
        print(f"Match {p[-50:]}: {hp == h1} ({hp[:16]})")
    except Exception as e:
        print(f"Error {p}: {e}")
