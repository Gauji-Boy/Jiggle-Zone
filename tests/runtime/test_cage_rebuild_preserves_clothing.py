"""Building a cage on a garment must not consume its clothing attachment.

    blender -b poc_cage_xpbd_kasumi.blend --python-exit-code 1 \
        --python tests/runtime/test_cage_rebuild_preserves_clothing.py

The add-on has to be installed and enabled, so this runs without `--factory-startup`.

3.0 names a clothing bind `Jiggle_SurfaceDeform` and a cage bind `Jiggle_Cage_SD_<vg>`; 2.1 used
`Giggle_SurfaceDeform` and `Giggle_Cage_SD_<vg>` for the same two jobs. `get_cage_sd_modifier`
briefly accepted the bare clothing name as a cage bind, so building or rebuilding a cage on a
garment that is also attached as clothing deleted the attachment without a word. This attaches a
real garment, gives it a zone of its own, and requires the attachment to survive both names.
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

BODY = "kasumi_body"
GARMENT = "leggins"
ZONE = "Giggle_Jiggle_Zone"
VG = "skirt_zone"

failures = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + (("  <- " + str(detail)) if detail else ""))
    if not condition:
        failures.append(name)


def surface_deforms(obj):
    return [m for m in obj.modifiers if m.type == 'SURFACE_DEFORM']


def attach_clothing():
    body = bpy.data.objects[BODY]
    garment = bpy.data.objects[GARMENT]
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    garment.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.context.scene.jiggle_settings.clothing_target_zone = ZONE
    return bpy.ops.jiggle.attach_clothing_proxy()


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def state(mod):
    return (mod.name, mod.target.name if mod.target else None, mod.vertex_group,
            mod.is_bound, mod.show_viewport, mod.show_render)


def diff(before_state, after_state):
    return "" if before_state == after_state else f"{after_state} != {before_state}"


print("BLENDER", bpy.app.version_string)
garment = bpy.data.objects[GARMENT]

# --- a garment attached as clothing ---------------------------------------------------------
check("clothing attach finished", attach_clothing() == {'FINISHED'})
sds = surface_deforms(garment)
check("attach leaves one clothing Surface Deform", len(sds) == 1, [m.name for m in sds])
clothing = sds[0]
check("it uses the 3.0 clothing name", clothing.name == "Jiggle_SurfaceDeform", clothing.name)
check("it is bound to a proxy", clothing.target is not None and clothing.target.name.endswith("_Proxy"),
      getattr(clothing.target, "name", None))

# 2.1 would have left the same modifier under the legacy name
clothing.name = "Giggle_SurfaceDeform"
before = state(clothing)

# --- the same garment also becomes a jiggle zone of its own ---------------------------------
vg = garment.vertex_groups.new(name=VG)
vg.add(list(range(len(garment.data.vertices))), 1.0, 'REPLACE')

activate(garment)
settings = bpy.context.scene.jiggle_settings
settings.new_zone_engine = 'WIGGY'
settings.new_zone_vg = VG
settings.new_zone_name = "Skirt"
check("garment zone created", bpy.ops.jiggle.add_zone() == {'FINISHED'},
      [m.name for m in garment.modifiers])
check("zone modifier exists", "Jiggle_Skirt" in garment.modifiers)

mods = g.get_jiggle_modifiers(garment)
settings.active_zone_index = mods.index(garment.modifiers["Jiggle_Skirt"])

# --- build the garment's cage: the attachment has to survive --------------------------------
check("cage generation finished", bpy.ops.jiggle.generate_cage() == {'FINISHED'},
      [m.name for m in garment.modifiers])
cage_bind = garment.modifiers.get("Jiggle_Cage_SD_" + VG)
check("garment got its own cage bind", cage_bind is not None and cage_bind.is_bound,
      [m.name for m in garment.modifiers])
check("cage bind targets the new cage",
      cage_bind is not None and cage_bind.target is not None
      and cage_bind.target.name == f"{GARMENT}_{VG}_Cage",
      getattr(cage_bind.target, "name", None) if cage_bind else None)
check("2.x clothing attachment survives cage generation",
      clothing.name in garment.modifiers, [m.name for m in garment.modifiers])
check("attachment state is untouched by cage generation", state(clothing) == before,
      diff(before, state(clothing)))

# --- rebuild under the 3.0 name --------------------------------------------------------------
clothing.name = "Jiggle_SurfaceDeform"
before = state(clothing)
check("cage rebuild finished", bpy.ops.jiggle.rebuild_cage() == {'FINISHED'},
      [m.name for m in garment.modifiers])
check("3.0 clothing attachment survives cage rebuild",
      clothing.name in garment.modifiers, [m.name for m in garment.modifiers])
check("attachment state is untouched by cage rebuild", state(clothing) == before,
      diff(before, state(clothing)))

rebuilt = garment.modifiers.get("Jiggle_Cage_SD_" + VG)
if rebuilt is not None:
    rebuilt.name = "Giggle_Cage_SD_" + VG
check("legacy cage bind name is still discovered",
      getattr(g.get_cage_sd_modifier(garment, VG), "name", None) == "Giggle_Cage_SD_" + VG,
      getattr(g.get_cage_sd_modifier(garment, VG), "name", None))

# --- discovery: bare clothing names are never cage binds -----------------------------------
bpy.ops.mesh.primitive_cube_add()
probe = bpy.context.active_object
probe.name = "Probe"
bare = probe.modifiers.new("Jiggle_SurfaceDeform", 'SURFACE_DEFORM')
check("3.0 clothing name is not a cage bind", g.get_cage_sd_modifier(probe, VG) is None)
check("3.0 clothing name is still recognised as a clothing bind", g.is_staged_proxy_sd(bare))
bare.name = "Giggle_SurfaceDeform"
check("2.x clothing name is not a cage bind", g.get_cage_sd_modifier(probe, VG) is None)
check("2.x clothing name is still recognised as a clothing bind", g.is_staged_proxy_sd(bare))

probe.modifiers.new("Jiggle_Cage_SD_" + VG, 'SURFACE_DEFORM')
check("current cage bind is discovered",
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None) == "Jiggle_Cage_SD_" + VG,
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None))
probe.modifiers["Jiggle_Cage_SD_" + VG].name = "Giggle_Cage_SD_" + VG
check("legacy cage bind is discovered",
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None) == "Giggle_Cage_SD_" + VG,
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None))
probe.modifiers["Giggle_Cage_SD_" + VG].name = "Giggle_Cage_SurfaceDeform"
check("legacy cage bind with a generic suffix is discovered",
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None) == "Giggle_Cage_SurfaceDeform",
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None))
# A Geometry Nodes cage modifier shares the name pattern; only a Surface Deform may match.
probe.modifiers.new("Jiggle_Cage_" + VG, 'NODES')
check("a cage-named non Surface Deform is skipped",
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None) == "Giggle_Cage_SurfaceDeform",
      getattr(g.get_cage_sd_modifier(probe, VG), "name", None))

print("RESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
sys.exit(1 if failures else 0)
