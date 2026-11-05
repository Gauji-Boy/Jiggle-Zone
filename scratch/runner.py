import sys
import traceback

try:
    with open(r"d:\Blender\Giggle\scratch\verify_audit_v121_complete.py", "r", encoding="utf-8") as f:
        code = f.read()
    exec(code, globals())
except Exception as e:
    with open(r"d:\Blender\Giggle\scratch\error.log", "w", encoding="utf-8") as err_f:
        traceback.print_exc(file=err_f)
    print("Logged exception to error.log")
    sys.exit(1)
