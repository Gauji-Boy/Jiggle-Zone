"""Re-attaching clothing must not leave a second, legacy Surface Deform behind.

    blender -b poc_cage_xpbd_kasumi.blend --factory-startup --python-exit-code 1 \
        --python tests/runtime/test_legacy_attach.py

The add-on is installed from jiggle-zone.zip by the caller (see tests/HANDOFF.md), so this runs
against the packaged code. A real 2.1 garment carries `Giggle_SurfaceDeform`; the cleanup used
to match only the 3.0 name, so an in-place upgrade kept both modifiers. This reproduces that
state without needing the 2.1 artifact: attach once, rename the result to the 2.x name, attach
again, and require a single bound modifier bound to the same proxy.
"""

import bpy
import sys

ZONE = "Giggle_Jiggle_Zone"
BODY = "kasumi_body"
GARMENT = "leggins"

failures = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + (("  <- " + str(detail)) if detail else ""))
    if not condition:
        failures.append(name)


def attach():
    body = bpy.data.objects[BODY]
    garment = bpy.data.objects[GARMENT]
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    garment.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.context.scene.jiggle_settings.clothing_target_zone = ZONE
    return bpy.ops.jiggle.attach_clothing_proxy()


def surface_deforms(obj):
    return [m for m in obj.modifiers if m.type == 'SURFACE_DEFORM']


def points(garment):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = garment.evaluated_get(dg)
    mesh = ev.to_mesh()
    pts = [v.co.copy() for v in mesh.vertices]
    ev.to_mesh_clear()
    return pts


def measure(garment, proxy):
    rest = points(garment)
    proxy.location.z += 0.10
    bpy.context.view_layer.update()
    moved = points(garment)
    proxy.location.z -= 0.10
    bpy.context.view_layer.update()
    return rest, moved


print("BLENDER", bpy.app.version_string)
garment = bpy.data.objects[GARMENT]

# --- first attach, then make it look like a garment attached by 2.1 ------------------------
check("first attach finished", attach() == {'FINISHED'})
sds = surface_deforms(garment)
check("first attach leaves one Surface Deform", len(sds) == 1, [m.name for m in sds])
proxy = sds[0].target
check("it is bound to a proxy", proxy is not None and proxy.name.endswith("_Proxy"),
      getattr(proxy, 'name', None))
rest_clean, moved_clean = measure(garment, proxy)

sds[0].name = "Giggle_SurfaceDeform"
print("simulated 2.1 stack:", [m.name for m in garment.modifiers])

# --- the upgrade path: attach again over the legacy modifier -------------------------------
check("second attach finished", attach() == {'FINISHED'})
sds = surface_deforms(garment)
print("upgraded stack:", [m.name for m in garment.modifiers])
check("upgrade leaves one Surface Deform", len(sds) == 1, [m.name for m in sds])
check("it uses the 3.0 name", [m.name for m in sds] == ["Jiggle_SurfaceDeform"],
      [m.name for m in sds])
check("no legacy Surface Deform survives", "Giggle_SurfaceDeform" not in garment.modifiers)
check("no temporary modifier survives",
      all("_tmp_" not in m.name for m in garment.modifiers),
      [m.name for m in garment.modifiers])
check("the survivor is bound", all(m.is_bound for m in sds), [m.is_bound for m in sds])

rest_upgrade, moved_upgrade = measure(garment, proxy)
delta_rest = max((a - b).length for a, b in zip(rest_clean, rest_upgrade))
delta_moved = max((a - b).length for a, b in zip(moved_clean, moved_upgrade))
check("rest shape is unchanged by the re-attach", delta_rest <= 1e-3, f"{delta_rest:.6f} m")
check("deformation is unchanged by the re-attach", delta_moved <= 1e-3, f"{delta_moved:.6f} m")

print("RESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
sys.exit(1 if failures else 0)
