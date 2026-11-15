"""Smoke test on a scene with no Jiggle setup: registration, operators, no tracebacks.

    blender -b <any.blend> --python-exit-code 1 --python tests/runtime/test_secondary_scene.py
"""

import sys
import traceback

import bpy

REQUIRED_OPS = (
    "bake_all_cages",
    "bake_selected_cage",
    "rebake_all",
    "rebake_sim",
    "bake_missing",
    "check_cache_validity",
    "clear_sim_cache",
)


def main():
    print("BLENDER", bpy.app.version_string, "FILE", bpy.data.filepath)
    print("objects:", len(bpy.data.objects),
          "armatures:", [o.name for o in bpy.data.objects if o.type == 'ARMATURE'])

    module = bpy.context.preferences.addons.get("bl_ext.user_default.jiggle_zone")
    if module is None:
        print("FAIL the add-on is not enabled in this Blender")
        return 1
    print("version:", getattr(module.module, "bl_info", {}).get("version"))

    available = [name for name in dir(bpy.ops.jiggle) if not name.startswith("_")]
    print("jiggle operators:", len(available))
    missing = [name for name in REQUIRED_OPS if name not in available]
    if missing:
        print("FAIL missing operators:", missing)
        return 1

    scene = bpy.context.scene
    print("frame range:", scene.frame_start, scene.frame_end)
    if not hasattr(scene, "jiggle_settings"):
        print("FAIL jiggle_settings missing on the scene")
        return 1

    print("PASS registration and operators on a scene without a Jiggle setup")
    return 0


try:
    sys.exit(main())
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    sys.exit(1)
