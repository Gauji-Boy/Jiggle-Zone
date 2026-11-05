import os
import zipfile

addon_dir = r"d:\Blender\Giggle\giggle_addon"
zip_path = r"d:\Blender\Giggle\giggle_addon.zip"

# Ensure no .pyc or __pycache__ exist
for root, dirs, files in os.walk(addon_dir):
    for d in list(dirs):
        if d == '__pycache__':
            shutil.rmtree(os.path.join(root, d))
            dirs.remove(d)

with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for root, dirs, files in os.walk(addon_dir):
        # Skip pycache if any
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in sorted(files):
            if file.endswith('.pyc') or file.endswith('.pyo'):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, os.path.dirname(addon_dir))
            # Normalize to forward slashes
            arcname = rel_path.replace(os.sep, '/')
            zf.write(full_path, arcname=arcname)
            print(f"Added: {arcname}")

print(f"\nSuccessfully created {zip_path} ({os.path.getsize(zip_path)} bytes)")

# Verify contents
with zipfile.ZipFile(zip_path, 'r') as zf:
    print("\nVerified ZIP archive entries:")
    for info in zf.infolist():
        print(f"  {info.filename} ({info.file_size:,} bytes)")
        assert not info.filename.endswith('.pyc')
        assert '__pycache__' not in info.filename
print("\nZIP verification passed 100%!")
