"""Both bundled Wiggy solver groups must work through the real code paths.

    blender -b --factory-startup --python-exit-code 1 \\
        --python tests/runtime/test_wiggy_versions.py

3.1 bundles `Wiggy 0.2.0` and keeps `Wiggy 0.1` for projects that already embed it.
Recognition used to be a hardcoded `name == "Wiggy 0.1"`, so the risk is not that the
predicate returns False — it is that a downstream path silently skips a 0.2 zone and
reports "no solver". These checks therefore drive presets, bake detection, cage lookup
and the Socket_2 attribute path for both versions, not just `is_wiggy_group`.

The module is imported from source and registered here, so the run is self-contained
and needs no installed add-on.
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


def section(title):
    print("\n# " + title)


def mesh_with_group(group_name, object_name, dense=False):
    if dense:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    else:
        bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    obj.name = object_name
    weights = obj.vertex_groups.new(name=group_name)
    weights.add(list(range(min(4, len(obj.data.vertices)))), 1.0, 'REPLACE')
    return obj


def bind_body_to(cage, suffix):
    """A body bound through a Jiggle-named Surface Deform; proves cage ownership structurally."""
    bpy.ops.mesh.primitive_cube_add()
    body = bpy.context.active_object
    body.name = f"Body_{suffix}"
    bind = body.modifiers.new(f"Jiggle_Cage_SD_{suffix}", 'SURFACE_DEFORM')
    bind.target = cage
    return body


def socket(mod, identifier):
    return getattr(mod.properties.inputs, identifier, None)


def snapshot(mod, identifiers):
    out = {}
    for identifier in identifiers:
        entry = socket(mod, identifier)
        out[identifier] = None if entry is None else (
            getattr(entry, "value", None),
            getattr(entry, "type", None),
            getattr(entry, "attribute_name", None),
        )
    return out


bpy.ops.wm.read_homefile(use_empty=True)
g.register()

old_group = g.ensure_nodetree("Wiggy 0.1")
new_group = g.ensure_nodetree("Wiggy 0.2.0")

# --- the allow-list itself -----------------------------------------------------------------
section("recognition")
check("0.1 is a supported group", g.is_wiggy_group(old_group), getattr(old_group, "name", None))
check("0.2.0 is a supported group", g.is_wiggy_group(new_group), getattr(new_group, "name", None))
check("None is not a supported group", not g.is_wiggy_group(None))
for lookalike in ("Wiggy 0.2", "Wiggy 0.3.0", "Wiggy Something", "Wiggy 0.2.0 copy", "wiggy 0.2.0"):
    group = bpy.data.node_groups.new(lookalike, "GeometryNodeTree")
    check(f"lookalike rejected: {lookalike!r}", not g.is_wiggy_group(group))

# --- asset selection ------------------------------------------------------------------------
section("asset selection")
check("0.2.0 resolves to its own file",
      g.ASSET_GROUP_FILES.get("Wiggy 0.2.0") == "Wiggy_0.2.0.blend",
      g.ASSET_GROUP_FILES.get("Wiggy 0.2.0"))
check("0.1 still resolves to its own file",
      g.ASSET_GROUP_FILES.get("Wiggy 0.1") == "Wiggy_0.1.blend",
      g.ASSET_GROUP_FILES.get("Wiggy 0.1"))
check("an unrelated Wiggy-like group loads nothing",
      g.ensure_nodetree("Wiggy Something Else") is None)
check("both groups coexist in one file",
      {"Wiggy 0.1", "Wiggy 0.2.0"} <= {group.name for group in bpy.data.node_groups})

# --- modifier recognition on real modifiers -------------------------------------------------
section("modifier recognition")
body = mesh_with_group("Zone", "Body")
legacy = body.modifiers.new("Jiggle_Legacy", 'NODES')
legacy.node_group = old_group
modern = body.modifiers.new("Jiggle_Modern", 'NODES')
modern.node_group = new_group

check("0.1 modifier is a jiggle modifier", g.is_jiggle_modifier(legacy))
check("0.2 modifier is a jiggle modifier", g.is_jiggle_modifier(modern))
check("both are enumerated",
      {m.name for m in g.get_jiggle_modifiers(body)} == {"Jiggle_Legacy", "Jiggle_Modern"},
      [m.name for m in g.get_jiggle_modifiers(body)])

# --- a new zone must be created on the new group --------------------------------------------
section("new zone creation")
settings = bpy.context.scene.jiggle_settings
fresh = mesh_with_group("Zone", "Fresh", dense=True)
settings.new_zone_engine = 'WIGGY'
settings.new_zone_vg = "Zone"
settings.new_zone_name = "Modern"
result = bpy.ops.jiggle.add_zone()
created = [m for m in fresh.modifiers if m.type == 'NODES']
check("add_zone finished", result == {'FINISHED'}, result)
check("new zone uses Wiggy 0.2.0",
      created and created[-1].node_group and created[-1].node_group.name == "Wiggy 0.2.0",
      [m.node_group.name if m.node_group else None for m in created])

# --- preset application must be identical on both groups ------------------------------------
section("preset application")
preset = g.PRESETS["REAL_BREASTS_NATURAL"]
identifiers = sorted(preset["values"])

old_zone = body.modifiers["Jiggle_Legacy"]
new_zone = body.modifiers["Jiggle_Modern"]
for mod in (old_zone, new_zone):
    for identifier, value in preset["values"].items():
        g.set_mod_socket(mod, identifier, value=value, sync_cage=False)

old_snapshot = snapshot(old_zone, identifiers)
new_snapshot = snapshot(new_zone, identifiers)
missing = [i for i in identifiers if old_snapshot[i] is None or new_snapshot[i] is None]
check("every preset socket exists on both groups", not missing, missing)
check("0.2 receives the same values as 0.1", old_snapshot == new_snapshot,
      {k: (old_snapshot[k], new_snapshot[k]) for k in identifiers if old_snapshot[k] != new_snapshot[k]})

softness = new_snapshot.get("Socket_33", (None,))[0]
check("0.2 softness matches the preset", abs(softness - preset["values"]["Socket_33"]) < 1e-4, softness)

# --- Socket_2 is an attribute on both versions ----------------------------------------------
section("Socket_2 attribute handling")
for label, mod in (("0.1", old_zone), ("0.2", new_zone)):
    result = g.set_mod_socket(mod, 'Socket_2', attribute="Chest_Weights", sync_cage=False)
    entry = socket(mod, "Socket_2")
    check(f"{label} Socket_2 accepts a vertex group name", result, result)
    check(f"{label} Socket_2 is an attribute socket",
          getattr(entry, "type", None) == 'ATTRIBUTE', getattr(entry, "type", None))
    check(f"{label} Socket_2 carries the group name",
          getattr(entry, "attribute_name", None) == "Chest_Weights",
          getattr(entry, "attribute_name", None))
    check(f"{label} Socket_2 refuses a bare number",
          g.set_mod_socket(mod, 'Socket_2', value=0.5, sync_cage=False) is False)

# --- bake detection and cage lookup ---------------------------------------------------------
section("bake detection")
bpy.ops.mesh.primitive_cube_add()
cage_old = bpy.context.active_object
cage_old.name = "Cage_Legacy"
cage_old.modifiers.new("Jiggle_Cage_XPBD", 'NODES').node_group = old_group
bind_body_to(cage_old, "legacy")

bpy.ops.mesh.primitive_cube_add()
cage_new = bpy.context.active_object
cage_new.name = "Cage_Modern"
cage_new.modifiers.new("Jiggle_Cage_XPBD", 'NODES').node_group = new_group
bind_body_to(cage_new, "modern")

for label, cage in (("0.1", cage_old), ("0.2", cage_new)):
    check(f"{label} cage is owned by jiggle", g.is_jiggle_owned_cage(cage))
    check(f"{label} cage starts without a cache", not g.cage_has_cache(cage))
    check(f"{label} cage has a physics hash", g.compute_physics_hash(cage) is not None)
    check(f"{label} cage status is readable", g.get_cage_bake_status(cage) is not None)
    check(f"{label} cage disk dirs are readable", isinstance(g.cage_disk_cache_dirs(cage), (list, tuple)),
          type(g.cage_disk_cache_dirs(cage)).__name__)

old_issues = g.preflight_validate_bake(bpy.context, [cage_old], 'PACKED', 1, 10)
new_issues = g.preflight_validate_bake(bpy.context, [cage_new], 'PACKED', 1, 10)
check("0.2 cage passes the same preflight as 0.1", len(old_issues) == len(new_issues),
      {"0.1": old_issues, "0.2": new_issues})

# --- an embedded 0.1 group is never swapped ------------------------------------------------
section("no silent replacement")
before = old_zone.node_group
g.ensure_nodetree("Wiggy 0.2.0")
check("existing 0.1 modifier keeps its group", old_zone.node_group is before,
      getattr(old_zone.node_group, "name", None))
check("0.1 group survives alongside 0.2", "Wiggy 0.1" in bpy.data.node_groups)

g.unregister()

print("\nRESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
sys.exit(1 if failures else 0)
