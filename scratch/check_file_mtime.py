import os
import glob
import datetime

path = r"E:\3D models\modles\Netosis_-_Kasumi\netosiskasumi_2.blend"
mtime = os.path.getmtime(path)
print(f"File {path} mtime: {datetime.datetime.fromtimestamp(mtime)}")

temp_autosaves = glob.glob(os.path.expanduser(r"~\AppData\Local\Temp\*.blend"))
temp_autosaves.sort(key=os.path.getmtime, reverse=True)
print("Recent autosaves:")
for a in temp_autosaves[:5]:
    print(f"  {a} ({datetime.datetime.fromtimestamp(os.path.getmtime(a))})")
