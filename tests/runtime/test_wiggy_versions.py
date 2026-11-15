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
import tempfile
import time
from types import SimpleNamespace

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


def interface_socket(group, identifier):
    return next(
        (item for item in group.interface.items_tree
         if getattr(item, "identifier", None) == identifier),
        None,
    )


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


class LayoutProbe:
    def __init__(self):
        self.properties = []

    def column(self):
        return self

    def prop(self, _data, identifier, **_kwargs):
        self.properties.append(identifier)


def draw_dynamics_properties():
    panel = SimpleNamespace(layout=LayoutProbe())
    g.VIEW3D_PT_jiggle_dynamics.draw(panel, bpy.context)
    return panel.layout.properties


def activate_zone(obj, mod):
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    settings = bpy.context.scene.jiggle_settings
    settings.active_zone_index = g.get_jiggle_modifiers(obj).index(mod)


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

# --- 0.2 return-wave controls are per modifier and survive save/reopen -------------------------
section("return-wave controls")
wave_properties = ("zone_return_wave", "zone_relax_time", "zone_decay")
wave_sockets = ("Socket_141", "Socket_142", "Socket_143")
wave_values = (0.37, 1.8, 0.62)
wave_ranges = ((0.0, 1.0), (0.05, 5.0), (0.0, 1.0))
wave_defaults = (0.0, 1.0, 0.5)
settings = bpy.context.scene.jiggle_settings

for prop_name in wave_properties:
    check(f"{prop_name} is registered", prop_name in settings.bl_rna.properties)

for prop_name, identifier, default, value_range in zip(
        wave_properties, wave_sockets, wave_defaults, wave_ranges):
    item = interface_socket(new_group, identifier)
    check(f"{identifier} asset default is preserved",
          item is not None and abs(float(item.default_value) - default) < 1e-5,
          getattr(item, "default_value", None))
    if prop_name in settings.bl_rna.properties:
        prop = settings.bl_rna.properties[prop_name]
        check(f"{prop_name} range matches the approved range",
              abs(prop.hard_min - value_range[0]) < 1e-6
              and abs(prop.hard_max - value_range[1]) < 1e-6,
              (prop.hard_min, prop.hard_max))

if "zone_decay" in settings.bl_rna.properties:
    decay_property = settings.bl_rna.properties["zone_decay"]
    check("Decay description is preserved exactly",
          decay_property.description
          == "How much weaker the wave comes back each time: 0.5 is half as strong, 1 is no return at all",
          decay_property.description)

activate_zone(body, new_zone)
wave_ui = draw_dynamics_properties()
check("0.2 dynamics UI shows all wave controls",
      set(wave_properties) <= set(wave_ui), wave_ui)
for identifier in wave_sockets:
    check(f"0.2 exposes {identifier}", socket(new_zone, identifier) is not None)

# This cage uses the same body/group naming that sync_socket_to_cage resolves.
cage = bpy.data.objects.new("Body_Zone_Cage", body.data.copy())
bpy.context.scene.collection.objects.link(cage)
cage_mod = cage.modifiers.new("Jiggle_Cage_XPBD", 'NODES')
cage_mod.node_group = new_group
g.set_mod_socket(new_zone, "Socket_2", attribute="Zone", sync_cage=False)
g.set_mod_socket(cage_mod, "Socket_2", attribute="Zone", sync_cage=False)

if all(prop in settings.bl_rna.properties for prop in wave_properties):
    # Simulate a valid baked cache so the real status helper can verify invalidation.
    baked_at = time.time()
    body["_jiggle_baked_at_timestamp"] = baked_at
    cage["_jiggle_baked_at_timestamp"] = baked_at
    body.pop("_jiggle_settings_modified_at", None)
    cage.pop("_jiggle_settings_modified_at", None)
    cache_mod = SimpleNamespace(
        type='NODES',
        node_group=new_group,
        bakes=[SimpleNamespace(data_blocks=[object()])],
    )
    cache_view = SimpleNamespace(type='MESH', modifiers=[cache_mod], get=cage.get)
    check("simulated existing cache starts baked",
          g.get_cage_bake_status(cache_view)[0] == 'BAKED',
          g.get_cage_bake_status(cache_view))

    for prop_name, identifier, value in zip(wave_properties, wave_sockets, wave_values):
        setattr(settings, prop_name, value)
        check(f"changing {prop_name} writes {identifier}",
              abs(float(g.get_mod_socket(new_zone, identifier)) - value) < 1e-5,
              g.get_mod_socket(new_zone, identifier))
        check(f"changing {prop_name} syncs to cage",
              abs(float(g.get_mod_socket(cage_mod, identifier)) - value) < 1e-5,
              g.get_mod_socket(cage_mod, identifier))

    check("wave setting change marks baked result outdated",
          g.get_cage_bake_status(cache_view)[0] == 'OUTDATED',
          g.get_cage_bake_status(cache_view))

    # Existing presets intentionally omit the new sockets; applying one must preserve them.
    preset_result = bpy.ops.jiggle.apply_preset(preset="REAL_BREASTS_NATURAL")
    after_preset = tuple(g.get_mod_socket(new_zone, identifier) for identifier in wave_sockets)
    check("preset reapplication succeeds", preset_result == {'FINISHED'}, preset_result)
    check("preset reapplication preserves wave settings",
          all(abs(float(actual) - expected) < 1e-5
              for actual, expected in zip(after_preset, wave_values)),
          after_preset)

    second_zone = body.modifiers.new("Jiggle_Second_Modern", 'NODES')
    second_zone.node_group = new_group
    g.set_mod_socket(second_zone, "Socket_2", attribute="Zone_Second", sync_cage=False)
    activate_zone(body, second_zone)
    second_values = (0.82, 3.2, 0.17)
    for prop_name, identifier, value in zip(wave_properties, wave_sockets, second_values):
        setattr(settings, prop_name, value)
        check(f"{prop_name} stores independently on the second zone",
              abs(float(g.get_mod_socket(second_zone, identifier)) - value) < 1e-5,
              g.get_mod_socket(second_zone, identifier))
    activate_zone(body, new_zone)
    first_values_after_switch = tuple(
        g.get_mod_socket(new_zone, identifier) for identifier in wave_sockets
    )
    check("switching zones restores the first zone's values",
          all(abs(float(actual) - expected) < 1e-5
              for actual, expected in zip(first_values_after_switch, wave_values)),
          first_values_after_switch)

# Wiggy 0.1 must not expose or acquire any of the 0.2-only sockets.
activate_zone(body, old_zone)
legacy_ui = draw_dynamics_properties()
check("0.1 dynamics UI hides wave controls",
      not (set(wave_properties) & set(legacy_ui)), legacy_ui)
if all(prop in settings.bl_rna.properties for prop in wave_properties):
    settings.zone_decay = 0.91
check("0.1 has no wave socket or fallback ID-property write",
      all(socket(old_zone, identifier) is None
          and g.get_mod_socket(old_zone, identifier) is None
          for identifier in wave_sockets),
      [g.get_mod_socket(old_zone, identifier) for identifier in wave_sockets])

# Exercise the exact 0.2 group name with one socket removed; partial interfaces stay hidden.
original_group_name = new_group.name
new_group.name = "_Wiggy_0.2.0_wave_test_original"
partial_group = new_group.copy()
partial_group.name = g.WIGGY_NEW_GROUP
missing_socket = next(
    item for item in partial_group.interface.items_tree
    if getattr(item, "identifier", None) == "Socket_143"
)
partial_group.interface.remove(missing_socket)
partial_obj = bpy.data.objects.new("Partial_Wave_Test", body.data.copy())
bpy.context.scene.collection.objects.link(partial_obj)
partial_mod = partial_obj.modifiers.new("Jiggle_Partial_Wave", 'NODES')
partial_mod.node_group = partial_group
activate_zone(partial_obj, partial_mod)
partial_ui = draw_dynamics_properties()
check("0.2 group missing one socket hides all wave controls",
      not (set(wave_properties) & set(partial_ui)), partial_ui)
partial_group.name = "Wiggy Partial Wave Test"
new_group.name = original_group_name

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

# Modifier input values, rather than scene-wide UI values, must persist in the .blend.
if all(prop in settings.bl_rna.properties for prop in wave_properties):
    activate_zone(body, new_zone)
    with tempfile.TemporaryDirectory(prefix="jiggle_wave_settings_", dir=ROOT) as temp_dir:
        blend_path = os.path.join(temp_dir, "wave_settings.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        bpy.ops.wm.open_mainfile(filepath=blend_path)
        reopened_body = bpy.data.objects.get("Body")
        reopened_zone = reopened_body.modifiers.get("Jiggle_Modern") if reopened_body else None
        reopened_values = tuple(
            g.get_mod_socket(reopened_zone, identifier) if reopened_zone else None
            for identifier in wave_sockets
        )
        check("save/reopen restores all three wave values",
              all(actual is not None and abs(float(actual) - expected) < 1e-5
                  for actual, expected in zip(reopened_values, wave_values)),
              reopened_values)

g.unregister()

print("\nRESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
sys.exit(1 if failures else 0)
