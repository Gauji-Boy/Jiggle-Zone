"""Wiggy 0.2.1 integration: Ripple, Smoothing and compatibility (headless, Blender 5.3).

    blender -b --factory-startup --python-exit-code 1 -t 1 \
        --python tests/runtime/test_wiggy_021_ripple.py

Imports the add-on from source, so no installed copy is required. The test is
self-contained and does not modify the installed extension.
"""

import hashlib
import importlib.util
import os
import sys
import tempfile
import time
from types import SimpleNamespace

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "jiggle_zone", "__init__.py")
ASSET = os.path.join(ROOT, "jiggle_zone", "assets", "Wiggy_0.2.1.blend")
ASSET_SHA256 = "4328183f843cd961fca0f836ac84cadb0e62dae285f97410877c07bcd82b8625"
SOCKETS = ("Socket_145", "Socket_146", "Socket_147")

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


def activate(obj):
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def activate_zone(obj, mod):
    activate(obj)
    settings = bpy.context.scene.jiggle_settings
    settings.active_zone_index = g.get_jiggle_modifiers(obj).index(mod)


def zone_host(name, group_name, vg_name="Zone"):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    obj.name = name
    vg = obj.vertex_groups.new(name=vg_name)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    mod = obj.modifiers.new(f"Jiggle_{name}", 'NODES')
    mod.node_group = g.ensure_nodetree(group_name)
    g.set_mod_socket(mod, 'Socket_2', attribute=vg_name, sync_cage=False)
    bpy.context.view_layer.update()
    return obj, mod


def socket_value(mod, identifier):
    return g.get_mod_socket(mod, identifier)


def close(actual, expected, tolerance=1e-5):
    return actual is not None and abs(float(actual) - float(expected)) < tolerance


def evaluated_coords(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [tuple(vertex.co) for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def max_coord_delta(first, second):
    if not first or not second or len(first) != len(second):
        return None
    return max(
        max(abs(a - b) for a, b in zip(point_a, point_b))
        for point_a, point_b in zip(first, second)
    )


def impact_zone(name, group_name, smooth_on):
    """Create a real zone through add_zone() and return (obj, mod, operator result)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0)
    obj = bpy.context.active_object
    obj.name = name
    vg = obj.vertex_groups.new(name="Zone")
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    settings = bpy.context.scene.jiggle_settings
    settings.new_zone_engine = 'WIGGY'
    settings.new_zone_vg = "Zone"
    settings.new_zone_name = name
    settings.new_zone_cage_mode = False
    result = bpy.ops.jiggle.add_zone()
    mod = next((m for m in obj.modifiers
                if m.type == 'NODES' and g.is_jiggle_modifier(m)), None)
    if mod is None:
        return obj, None, result
    if group_name != g.WIGGY_NEW_GROUP:
        mod.node_group = g.ensure_nodetree(group_name)
    activate_zone(obj, mod)
    if g.supports_wiggy_ripple(mod):
        settings.zone_ripple = 0.9
        settings.zone_ripple_speed = 3.0
        settings.zone_ripple_fade = 0.1
    settings.zone_post_smoothing = bool(smooth_on)
    return obj, mod, result


def run_impact(obj):
    """Jolt a zone with translation + rotation and sample its evaluated mesh per frame."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    scene.frame_set(1)
    obj.rotation_mode = 'XYZ'
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.keyframe_insert(data_path='location', frame=1)
    obj.keyframe_insert(data_path='rotation_euler', frame=1)
    obj.location = (0.0, 0.0, 2.5)
    obj.rotation_euler = (0.0, 0.0, 0.9)
    obj.keyframe_insert(data_path='location', frame=2)
    obj.keyframe_insert(data_path='rotation_euler', frame=2)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.keyframe_insert(data_path='location', frame=3)
    obj.keyframe_insert(data_path='rotation_euler', frame=3)
    obj.keyframe_insert(data_path='location', frame=10)
    obj.keyframe_insert(data_path='rotation_euler', frame=10)
    sampled = {}
    for frame in range(1, 11):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        sampled[frame] = evaluated_coords(obj, depsgraph)
    return sampled


class LayoutProbe:
    def __init__(self):
        self.properties = []
        self.enabled_states = []
        self.labels = []

    def column(self):
        return self

    def box(self):
        return self

    def row(self, **_kwargs):
        return self

    def prop(self, _data, identifier, **_kwargs):
        self.properties.append(identifier)

    def label(self, text="", **_kwargs):
        self.labels.append(text)

    def separator(self, **_kwargs):
        pass

    @property
    def enabled(self):
        return True

    @enabled.setter
    def enabled(self, value):
        self.enabled_states.append(bool(value))


def draw_dynamics():
    probe = LayoutProbe()
    g.VIEW3D_PT_jiggle_dynamics.draw(SimpleNamespace(layout=probe), bpy.context)
    return probe


def draw_shape():
    probe = LayoutProbe()
    g.VIEW3D_PT_jiggle_shape.draw(SimpleNamespace(layout=probe), bpy.context)
    return probe


bpy.ops.wm.read_homefile(use_empty=True)
g.register()

# --- asset and constants --------------------------------------------------------------------
section("asset and constants")
with open(ASSET, "rb") as handle:
    asset_hash = hashlib.sha256(handle.read()).hexdigest()
check("0.2.1 asset hash matches validated candidate", asset_hash == ASSET_SHA256, asset_hash)
check("new zones select Wiggy 0.2.1", g.WIGGY_NEW_GROUP == "Wiggy 0.2.1", g.WIGGY_NEW_GROUP)
check("0.2.1 is recognised", g.is_wiggy_group(g.ensure_nodetree("Wiggy 0.2.1")))
check("0.2.1 maps to its own asset",
      g.ASSET_GROUP_FILES.get("Wiggy 0.2.1") == "Wiggy_0.2.1.blend")
check("Collider mapping unchanged", g.ASSET_GROUP_FILES.get("Collider") == "Wiggy_0.2.0.blend")
check("Wiggy Wind mapping unchanged", g.ASSET_GROUP_FILES.get("Wiggy Wind") == "Wiggy_0.2.0.blend")
check("Back Faces mapping unchanged", g.ASSET_GROUP_FILES.get("Back Faces") == "BackFaces.blend")

# --- new zone defaults and socket mapping ---------------------------------------------------
section("new zone defaults and socket mapping")
settings = bpy.context.scene.jiggle_settings
settings.new_zone_engine = 'WIGGY'
settings.new_zone_vg = "Zone"
settings.new_zone_name = "RippleDefault"
fresh, fresh_mod = zone_host("Fresh", "Wiggy 0.2.1")
activate_zone(fresh, fresh_mod)
check("fresh zone uses 0.2.1", fresh_mod.node_group.name == g.WIGGY_NEW_GROUP)
check("Ripple socket default is 0.0", close(socket_value(fresh_mod, "Socket_145"), 0.0))
check("Ripple Speed socket default is 1.5", close(socket_value(fresh_mod, "Socket_146"), 1.5))
check("Ripple Fade socket default is 0.08", close(socket_value(fresh_mod, "Socket_147"), 0.08))
check("RNA Ripple default reads the socket", close(settings.zone_ripple, 0.0), settings.zone_ripple)
check("RNA Ripple Speed default reads the socket", close(settings.zone_ripple_speed, 1.5))
check("RNA Ripple Fade default reads the socket", close(settings.zone_ripple_fade, 0.08))
check("ripple support detected", g.supports_wiggy_ripple(fresh_mod))

# --- independent per-zone settings ----------------------------------------------------------
section("per-zone independence")
other, other_mod = zone_host("Other", "Wiggy 0.2.1")
activate_zone(fresh, fresh_mod)
settings.zone_ripple = 1.0
settings.zone_ripple_speed = 2.5
settings.zone_ripple_fade = 0.2
activate_zone(other, other_mod)
settings.zone_ripple = 0.25
settings.zone_ripple_speed = 4.0
settings.zone_ripple_fade = 0.5
check("zone A keeps its Ripple", close(socket_value(fresh_mod, "Socket_145"), 1.0))
check("zone B keeps its own Ripple", close(socket_value(other_mod, "Socket_145"), 0.25))
activate_zone(fresh, fresh_mod)
check("reactivating zone A restores its UI values",
      close(settings.zone_ripple, 1.0) and close(settings.zone_ripple_speed, 2.5)
      and close(settings.zone_ripple_fade, 0.2),
      (settings.zone_ripple, settings.zone_ripple_speed, settings.zone_ripple_fade))

# --- UI gating ------------------------------------------------------------------------------
section("UI")
probe = draw_dynamics()
check("Ripple controls are shown for 0.2.1",
      all(prop in probe.properties for prop in ("zone_ripple", "zone_ripple_speed", "zone_ripple_fade")),
      probe.properties)
activate_zone(other, other_mod)
settings.zone_ripple = 0.0
probe_off = draw_dynamics()
check("Speed and fade are disabled while Ripple is zero",
      False in probe_off.enabled_states and "zone_ripple" in probe_off.properties,
      probe_off.enabled_states)
settings.zone_ripple = 0.5
probe_on = draw_dynamics()
check("Speed and fade re-enable above zero",
      all(probe_on.enabled_states) and True in probe_on.enabled_states,
      probe_on.enabled_states)

# --- cache invalidation ---------------------------------------------------------------------
section("cache invalidation")
activate_zone(fresh, fresh_mod)
hash_before = g.compute_physics_hash(fresh)
fresh["_jiggle_baked_at_timestamp"] = 1000.0
fresh["_jiggle_settings_modified_at"] = 0.0
settings.zone_ripple = 0.75
check("changing Ripple invalidates the cache",
      fresh.get("_jiggle_settings_modified_at", 0) > fresh["_jiggle_baked_at_timestamp"],
      (fresh.get("_jiggle_settings_modified_at"), fresh["_jiggle_baked_at_timestamp"]))
check("changing Ripple changes the physics fingerprint",
      g.compute_physics_hash(fresh) != hash_before)
before_smooth_hash = g.compute_physics_hash(fresh)
settings.zone_post_smoothing = True
check("changing Smoothing changes the physics fingerprint",
      g.compute_physics_hash(fresh) != before_smooth_hash)
settings.zone_post_smoothing = False

# --- smoothing socket -----------------------------------------------------------------------
section("post-simulation smoothing")
check("0.2.1 exposes Socket_98", g.supports_wiggy_smoothing(fresh_mod))
check("Smoothing defaults off", socket_value(fresh_mod, "Socket_98") is False)
settings.zone_post_smoothing = True
check("Smoothing maps to Socket_98", socket_value(fresh_mod, "Socket_98") is True)
probe_shape = draw_shape()
check("Smoothing toggle is drawn for Wiggy zones",
      "zone_post_smoothing" in probe_shape.properties, probe_shape.properties)

# --- coexistence with older solvers ---------------------------------------------------------
section("coexistence with older solvers")
legacy, legacy_mod = zone_host("Legacy", "Wiggy 0.1")
older, older_mod = zone_host("Older", "Wiggy 0.2.0")
check("0.1 zone keeps its group", legacy_mod.node_group.name == "Wiggy 0.1")
check("0.2.0 zone keeps its group", older_mod.node_group.name == "Wiggy 0.2.0")
check("all three groups are in the scene",
      {"Wiggy 0.1", "Wiggy 0.2.0", "Wiggy 0.2.1"}
      <= {group.name for group in bpy.data.node_groups})
check("older groups do not gain ripple sockets",
      not g.supports_wiggy_ripple(legacy_mod) and not g.supports_wiggy_ripple(older_mod))
check("older groups keep collapse/wave controls",
      g.supports_wiggy_wave_settings(older_mod) and g.supports_wiggy_collider_slots(older_mod))
activate_zone(legacy, legacy_mod)
check("0.1 ripple property reads as off", close(settings.zone_ripple, 0.0))
check("0.1 has no ripple UI", "zone_ripple" not in draw_dynamics().properties)
activate_zone(older, older_mod)
check("0.2.0 has no ripple UI", "zone_ripple" not in draw_dynamics().properties)
check("0.2.0 still has wave UI", "zone_return_wave" in draw_dynamics().properties)

# Smoothing is gated on Socket_98, not the version name, because 0.1 and 0.2.0 also
# expose it. Check the real read/write path on each older group, not just 0.2.1.
for label, host, host_mod in (("0.1", legacy, legacy_mod), ("0.2.0", older, older_mod)):
    activate_zone(host, host_mod)
    check(f"{label} exposes Socket_98", g.supports_wiggy_smoothing(host_mod))
    check(f"{label} Smoothing defaults off", socket_value(host_mod, "Socket_98") is False)
    settings.zone_post_smoothing = True
    check(f"{label} Smoothing writes Socket_98", socket_value(host_mod, "Socket_98") is True)
    check(f"{label} draws the Smoothing toggle",
          "zone_post_smoothing" in draw_shape().properties, draw_shape().properties)
    settings.zone_post_smoothing = False
    check(f"{label} Smoothing clears back to off", socket_value(host_mod, "Socket_98") is False)
activate_zone(fresh, fresh_mod)

for obj in (fresh, other, legacy, older):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    check(f"{obj.name} evaluates with vertices", mesh is not None and len(mesh.vertices) > 0,
          len(mesh.vertices) if mesh else None)
    evaluated.to_mesh_clear()

# --- back faces with a 0.2.1 zone -----------------------------------------------------------
section("back faces with 0.2.1")
bpy.ops.mesh.primitive_grid_add(x_subdivisions=6, y_subdivisions=6, size=2.0)
collider = bpy.context.active_object
collider.name = "ColliderFor021"
collider_mod = collider.modifiers.new("Collider", 'NODES')
collider_mod.node_group = g.ensure_nodetree("Collider")
bpy.context.view_layer.update()
collection = bpy.data.collections.new("Jiggle_Colliders_021")
bpy.context.scene.collection.children.link(collection)
collection.objects.link(collider)
g.set_mod_socket(fresh_mod, "Socket_7", value=collection, sync_cage=False)
g.set_mod_socket(fresh_mod, "Socket_132", value=collider, sync_cage=False)
for index, poly in enumerate(collider.data.polygons):
    poly.select = index == 5
activate(collider)
result = bpy.ops.jiggle.mark_back_faces()
check("mark back faces succeeds on a 0.2.1 collider", result == {'FINISHED'}, result)
back_mod = g.get_back_face_modifier(collider)
check("back-face filter modifier exists", back_mod is not None)
check("back-face mask is not stale",
      back_mod is not None
      and not collider.get(getattr(g, "BACK_FACE_STALE_KEY", "_jiggle_back_face_stale"), False),
      getattr(g, "BACK_FACE_STALE_KEY", None))
check("Back Faces asset is unchanged", g.ASSET_GROUP_FILES.get("Back Faces") == "BackFaces.blend")

# --- behavioural smoothing under an impact ---------------------------------------------------
section("behavioural smoothing under impact")
original_cage_mode = settings.new_zone_cage_mode
for label, group_name in (("0.2.1", g.WIGGY_NEW_GROUP),
                          ("0.1", "Wiggy 0.1"),
                          ("0.2.0", "Wiggy 0.2.0")):
    slug = label.replace('.', '_')
    off_obj, off_mod, off_result = impact_zone(f"Impact_{slug}_Off", group_name, False)
    on_obj, on_mod, on_result = impact_zone(f"Impact_{slug}_On", group_name, True)
    check(f"{label} impact zone pair created through add_zone",
          off_result == {'FINISHED'} and on_result == {'FINISHED'}
          and off_mod is not None and on_mod is not None,
          (off_result, on_result))
    check(f"{label} smoothing is on only for the second impact zone",
          socket_value(off_mod, "Socket_98") is False
          and socket_value(on_mod, "Socket_98") is True,
          (socket_value(off_mod, "Socket_98"), socket_value(on_mod, "Socket_98")))
    try:
        frames_off = run_impact(off_obj)
        frames_on = run_impact(on_obj)
        deltas = [max_coord_delta(frames_off[frame], frames_on[frame])
                  for frame in sorted(frames_off)]
        biggest = max((delta for delta in deltas if delta is not None), default=0.0)
        check(f"{label} post-smoothing changes evaluated impact deformation",
              biggest > 1e-6, biggest)
    except Exception as exc:
        check(f"{label} post-smoothing changes evaluated impact deformation",
              False, f"impact evaluation raised {exc}")
settings.new_zone_cage_mode = original_cage_mode

# --- cage XPBD end to end --------------------------------------------------------------------
section("cage XPBD end to end")
settings.new_zone_cage_mode = True
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
cage_body = bpy.context.active_object
cage_body.name = "CageBody021"
cage_vg = cage_body.vertex_groups.new(name="Zone")
cage_vg.add(list(range(len(cage_body.data.vertices))), 1.0, 'REPLACE')
settings.new_zone_engine = 'WIGGY'
settings.new_zone_vg = "Zone"
settings.new_zone_name = "CageZone021"
cage_result = bpy.ops.jiggle.add_zone()
check("cage zone created through add_zone", cage_result == {'FINISHED'}, cage_result)
body_mod = next((m for m in cage_body.modifiers
                 if m.type == 'NODES' and g.is_jiggle_modifier(m)), None)
check("cage body solver uses 0.2.1",
      body_mod is not None and body_mod.node_group.name == g.WIGGY_NEW_GROUP,
      getattr(body_mod.node_group, "name", None) if body_mod else None)
check("add_zone produced an active cage",
      body_mod is not None and g.is_zone_in_cage_mode(cage_body, body_mod),
      g.get_zone_cage_error(body_mod) if body_mod else None)
cage_obj = g.get_zone_cage_object(cage_body, "Zone") if body_mod else None
cage_mod = next(
    (m for m in cage_obj.modifiers
     if m.type == 'NODES' and m.node_group and g.is_wiggy_group(m.node_group)),
    None,
) if cage_obj else None
check("cage solver uses 0.2.1",
      cage_mod is not None and cage_mod.node_group.name == g.WIGGY_NEW_GROUP,
      getattr(cage_mod.node_group, "name", None) if cage_mod else None)

activate_zone(cage_body, body_mod)
baseline = {
    "zone_ripple": ("Socket_145", 0.4),
    "zone_ripple_speed": ("Socket_146", 2.0),
    "zone_ripple_fade": ("Socket_147", 0.1),
    "zone_post_smoothing": ("Socket_98", True),
}
for prop, (_socket, value) in baseline.items():
    setattr(settings, prop, value)
check("initial four settings propagate to the cage modifier",
      cage_mod is not None and all(
          close(socket_value(cage_mod, socket), value)
          for socket, value in baseline.values()),
      tuple(socket_value(cage_mod, socket) for socket, _ in baseline.values()) if cage_mod else None)
check("smoothing area mask mirrors the zone group on the cage",
      cage_mod is not None and g.get_mod_socket_attribute_name(cage_mod, "Socket_99") == "Zone",
      g.get_mod_socket_attribute_name(cage_mod, "Socket_99") if cage_mod else None)

# Background Blender cannot produce simulation cache blocks, so validate against a view that
# presents one while delegating all real data (including modifier inputs) to the cage.
class _CachedModifier:
    def __init__(self, mod):
        self._mod = mod

    def __getattr__(self, name):
        return getattr(self._mod, name)

    @property
    def bakes(self):
        return [SimpleNamespace(data_blocks=[object()])]


class _CachedCageView:
    def __init__(self, cage):
        self._cage = cage
        self._mods = [
            _CachedModifier(m) if (m.type == 'NODES' and m.node_group and g.is_wiggy_group(m.node_group)) else m
            for m in cage.modifiers
        ]

    def __getattr__(self, name):
        return getattr(self._cage, name)

    def get(self, key, default=None):
        return self._cage.get(key, default)

    def __getitem__(self, key):
        return self._cage[key]

    def __setitem__(self, key, value):
        self._cage[key] = value

    def pop(self, key, *args):
        return self._cage.pop(key, *args)

    @property
    def modifiers(self):
        return self._mods


scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 3
settings.bake_storage_mode = 'PACKED'
settings.bake_use_scene_range = True
activate_zone(cage_body, body_mod)
g.save_zone_bake_fingerprint(cage_obj, bpy.context, 'PACKED', 1, 3)
cache_view = _CachedCageView(cage_obj) if cage_obj else None
check("simulated cage cache starts valid",
      g.check_cage_validity(cache_view, bpy.context)[0] == 'BAKED',
      g.check_cage_validity(cache_view, bpy.context) if cache_view else None)

changes = {
    "zone_ripple": ("Socket_145", 0.77),
    "zone_ripple_speed": ("Socket_146", 3.4),
    "zone_ripple_fade": ("Socket_147", 0.22),
    "zone_post_smoothing": ("Socket_98", False),
}
for prop, (socket, value) in changes.items():
    before_hash = g.compute_physics_hash(cage_obj)
    setattr(settings, prop, value)
    check(f"{prop} propagates to the cage modifier",
          close(socket_value(cage_mod, socket), value),
          (socket_value(cage_mod, socket), value))
    check(f"{prop} changes the cage physics hash",
          g.compute_physics_hash(cage_obj) != before_hash)
    status, reason = g.check_cage_validity(cache_view, bpy.context)
    check(f"{prop} marks the baked cage OUTDATED for a physics change",
          status == 'OUTDATED' and 'Physics' in reason, (status, reason))

activate_zone(cage_body, body_mod)
rebuild_result = bpy.ops.jiggle.rebuild_cage()
check("cage rebuild succeeds", rebuild_result == {'FINISHED'}, rebuild_result)
rebuilt_cage = g.get_zone_cage_object(cage_body, "Zone")
rebuilt_mod = next(
    (m for m in rebuilt_cage.modifiers
     if m.type == 'NODES' and m.node_group and g.is_wiggy_group(m.node_group)),
    None,
) if rebuilt_cage else None
check("rebuilt cage still uses 0.2.1",
      rebuilt_mod is not None and rebuilt_mod.node_group.name == g.WIGGY_NEW_GROUP,
      getattr(rebuilt_mod.node_group, "name", None) if rebuilt_mod else None)
surviving = tuple(socket_value(rebuilt_mod, socket) if rebuilt_mod else None
                  for socket in ("Socket_145", "Socket_146", "Socket_147", "Socket_98"))
check("rebuild preserves ripple and smoothing values",
      all(close(actual, expected) for actual, expected
          in zip(surviving, (0.77, 3.4, 0.22, False))),
      surviving)

# --- negative gating ------------------------------------------------------------------------
section("negative gating")
partial_source = g.ensure_nodetree(g.WIGGY_NEW_GROUP)
original_group_name = partial_source.name
partial_source.name = "_Wiggy_021_gating_original"
partial_group = partial_source.copy()
partial_group.name = original_group_name
socket_147 = next(item for item in partial_group.interface.items_tree
                  if getattr(item, "identifier", None) == "Socket_147")
partial_group.interface.remove(socket_147)
bpy.ops.mesh.primitive_cube_add()
partial_obj = bpy.context.active_object
partial_obj.name = "PartialRipple021"
partial_mod = partial_obj.modifiers.new("Jiggle_PartialRipple", 'NODES')
partial_mod.node_group = partial_group
check("0.2.1 group without Socket_147 loses ripple support",
      not g.supports_wiggy_ripple(partial_mod))
partial_group.name = "Wiggy 0.2.1 Partial Ripple Test"
partial_source.name = original_group_name

for label, host, host_mod in (("0.1", legacy, legacy_mod), ("0.2.0", older, older_mod)):
    activate_zone(host, host_mod)
    settings.zone_ripple = 0.95
    try:
        id_props = [key for key in host_mod.keys() if key.startswith("Socket_145")]
    except (TypeError, AttributeError):
        # New-style modifier inputs do not expose ID properties at all.
        id_props = []
    check(f"{label} ripple write creates no Socket_145 fallback",
          not g.supports_wiggy_ripple(host_mod)
          and g.get_mod_socket_prop(host_mod, "Socket_145") is None
          and not id_props,
          id_props)

# --- recipe operations preserve ripple and smoothing -----------------------------------------
section("preset / support / action-safety preservation")
activate_zone(fresh, fresh_mod)
settings.zone_ripple = 0.58
settings.zone_ripple_speed = 2.7
settings.zone_ripple_fade = 0.19
settings.zone_post_smoothing = True
preserved_sockets = ("Socket_145", "Socket_146", "Socket_147", "Socket_98")
expected = tuple(socket_value(fresh_mod, socket) for socket in preserved_sockets)
for label, operation in (
    ("preset", lambda: bpy.ops.jiggle.apply_preset(preset="REAL_BREASTS_NATURAL")),
    ("support level", lambda: bpy.ops.jiggle.apply_support_level(level="FIRM")),
    ("action safety", lambda: bpy.ops.jiggle.apply_action_safety()),
):
    activate_zone(fresh, fresh_mod)
    result = operation()
    actual = tuple(socket_value(fresh_mod, socket) for socket in preserved_sockets)
    check(f"{label} preserves user ripple and smoothing values",
          result == {'FINISHED'}
          and all(close(value, wanted) for value, wanted in zip(actual, expected)),
          (result, actual, expected))

# --- clothing workflow ----------------------------------------------------------------------
section("clothing workflow")
activate_zone(fresh, fresh_mod)
settings.zone_ripple = 0.66
settings.zone_ripple_speed = 2.2
settings.zone_ripple_fade = 0.14
settings.zone_post_smoothing = True
clothing_sockets = ("Socket_145", "Socket_146", "Socket_147", "Socket_98")
clothing_expected = tuple(socket_value(fresh_mod, socket) for socket in clothing_sockets)
bpy.ops.mesh.primitive_cube_add()
cloth = bpy.context.active_object
cloth.name = "Garment021"
cloth.location = (0.0, 0.0, 0.0)
activate(fresh)
cloth.select_set(True)
result = bpy.ops.jiggle.copy_zone_to_clothing()
check("copy zone to clothing succeeds with 0.2.1", result == {'FINISHED'}, result)
cloth_mod = next((m for m in cloth.modifiers if m.type == 'NODES'), None)
check("garment receives the same solver group",
      cloth_mod is not None and cloth_mod.node_group.name == "Wiggy 0.2.1",
      cloth_mod.node_group.name if cloth_mod else None)
check("garment keeps all four ripple/smoothing socket values",
      cloth_mod is not None and all(
          close(socket_value(cloth_mod, socket), wanted)
          for socket, wanted in zip(clothing_sockets, clothing_expected)),
      (tuple(socket_value(cloth_mod, socket) for socket in clothing_sockets)
       if cloth_mod else None, clothing_expected))

# The same 0.2.1 values must also survive the proxy path used by attach_clothing_proxy.
activate(fresh)
cloth.select_set(True)
settings.clothing_target_zone = fresh_mod.name
try:
    attach_result = bpy.ops.jiggle.attach_clothing_proxy()
    attach_error = ""
except Exception as exc:
    attach_result = {'CANCELLED'}
    attach_error = str(exc)
check("attach clothing proxy succeeds on a 0.2.1 zone",
      attach_result == {'FINISHED'}, (attach_result, attach_error))
proxy = bpy.data.objects.get("Fresh_Zone_Proxy")
proxy_mod = next(
    (m for m in proxy.modifiers
     if m.type == 'NODES' and m.node_group and g.is_wiggy_group(m.node_group)),
    None,
) if proxy else None
check("clothing proxy inherits the 0.2.1 group",
      proxy_mod is not None and proxy_mod.node_group.name == "Wiggy 0.2.1",
      getattr(proxy_mod.node_group, "name", None) if proxy_mod else None)
check("clothing proxy inherits Ripple and Smoothing values",
      proxy_mod is not None and all(
          close(socket_value(proxy_mod, socket), wanted)
          for socket, wanted in zip(clothing_sockets, clothing_expected)),
      (tuple(socket_value(proxy_mod, socket) for socket in clothing_sockets)
       if proxy_mod else None, clothing_expected))

# --- save/reopen persistence ----------------------------------------------------------------
section("save/reopen")
activate_zone(fresh, fresh_mod)
settings.zone_ripple = 0.42
settings.zone_ripple_speed = 3.3
settings.zone_ripple_fade = 0.11
settings.zone_post_smoothing = True
with tempfile.TemporaryDirectory(prefix="jiggle_021_ripple_", dir=ROOT) as temp_dir:
    blend_path = os.path.join(temp_dir, "ripple.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    reopened = bpy.data.objects.get("Fresh")
    reopened_mod = reopened.modifiers.get("Jiggle_Fresh") if reopened else None
    values = tuple(socket_value(reopened_mod, sid) if reopened_mod else None for sid in SOCKETS)
    check("save/reopen restores all three ripple values",
          all(close(actual, expected) for actual, expected in zip(values, (0.42, 3.3, 0.11))),
          values)
    check("save/reopen restores smoothing",
          reopened_mod is not None and socket_value(reopened_mod, "Socket_98") is True)

g.unregister()
print("\nRESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
sys.exit(1 if failures else 0)
