"""Legacy 2.x naming must still be recognised by 3.x discovery.

    blender -b --factory-startup --python-exit-code 1 --python tests/runtime/test_legacy_names.py

2.1 named every modifier it created `Giggle_*`. 3.0 creates `Jiggle_*`. Discovery has to accept
both, or an existing project opens looking empty and nothing can be baked.
"""

import importlib.util
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "jiggle_zone", "__init__.py")

SPEC = importlib.util.spec_from_file_location("jiggle_under_test", SOURCE)
g = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g)

failures = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + (("  <- " + str(detail)) if detail else ""))
    if not condition:
        failures.append(name)


# --- name helpers -------------------------------------------------------------------------
check("2.x name recognised", g.is_jiggle_addon_name("Giggle_Cage_XPBD"))
check("3.x name recognised", g.is_jiggle_addon_name("Jiggle_Cage_XPBD"))
check("foreign name rejected", not g.is_jiggle_addon_name("Wiggy Wind"))
check("2.x prefix stripped", g.strip_jiggle_prefix("Giggle_Butt_Zone") == "Butt_Zone",
      g.strip_jiggle_prefix("Giggle_Butt_Zone"))
check("3.x prefix stripped", g.strip_jiggle_prefix("Jiggle_Butt_Zone") == "Butt_Zone")
check("no prefix left intact", g.strip_jiggle_prefix("Butt_Zone") == "Butt_Zone")

# --- a 2.x cage: no metadata, ownership proven only by the bind modifier --------------------
bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene

bpy.ops.mesh.primitive_cube_add()
cage = bpy.context.active_object
cage.name = "Chest_Cage"
group = bpy.data.node_groups.new("Wiggy 0.1", "GeometryNodeTree")
cage.modifiers.new("Giggle_Cage_XPBD", 'NODES').node_group = group

bpy.ops.mesh.primitive_cube_add()
body = bpy.context.active_object
body.name = "Body"
bind = body.modifiers.new("Giggle_Cage_SD_chest", 'SURFACE_DEFORM')
bind.target = cage

found = g.get_cage_sd_modifier(body, "chest")
check("legacy bind modifier found", found is not None and found.name == bind.name,
      found.name if found else None)
check("legacy cage is a bind target", cage in g.get_jiggle_cage_bind_targets(scene.objects))
check("legacy cage is discovered", cage in g.get_jiggle_simulation_objects(bpy.context, body),
      [o.name for o in g.get_jiggle_simulation_objects(bpy.context, body)])

# --- the same scene with 3.x names must behave identically --------------------------------
bind.name = "Jiggle_Cage_SD_chest"
cage.modifiers["Giggle_Cage_XPBD"].name = "Jiggle_Cage_XPBD"
found = g.get_cage_sd_modifier(body, "chest")
check("3.x bind modifier found", found is not None and found.name == bind.name,
      found.name if found else None)
check("3.x cage is discovered", cage in g.get_jiggle_simulation_objects(bpy.context, body))

# --- modifier name alone marks a zone, even with an unrecognised node group --------------
zone_group = bpy.data.node_groups.new("Unrelated Group", "GeometryNodeTree")
body.modifiers.new("Giggle_Thigh_Zone", 'NODES').node_group = zone_group
check("legacy zone modifier recognised", g.is_jiggle_modifier(body.modifiers["Giggle_Thigh_Zone"]))

# --- a previous clothing attach's Surface Deform is stale in both naming eras -------------
# Leaving the 2.x one alive leaves two bound Surface Deforms after a 3.0 re-attach, and the
# stale bind takes over the moment the new one is disabled. A cage bind must never match.
stale = body.modifiers.new("Giggle_SurfaceDeform", 'SURFACE_DEFORM')
check("2.x staged proxy deform is stale", g.is_staged_proxy_sd(stale))
stale.name = "Jiggle_SurfaceDeform"
check("3.x staged proxy deform is stale", g.is_staged_proxy_sd(stale))
stale.name = "_tmp_Giggle_SurfaceDeform"
check("2.x leftover staged deform is stale", g.is_staged_proxy_sd(stale))
check("cage bind is not stale", not g.is_staged_proxy_sd(bind))
check("cage surface deform is not stale",
      not g.is_staged_proxy_sd(cage.modifiers.new("Jiggle_Cage_SurfaceDeform", 'SURFACE_DEFORM')))
check("follow node group is not stale",
      not g.is_staged_proxy_sd(cage.modifiers["Jiggle_Cage_XPBD"]))

print("RESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
sys.exit(1 if failures else 0)
