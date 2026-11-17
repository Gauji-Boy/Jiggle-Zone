"""Back-face filter: exact per-face collider exclusion, and fail-safe on topology change.

    blender -b --factory-startup --python-exit-code 1 \\
        --python tests/runtime/test_back_face_filter.py

`Mark Back Faces` writes a comma-separated mask (one `1`/`0` per face index) into a hidden
input of the bundled `Back Faces` node group, which stores the solver's `wiggy_sheet_back`
face attribute. `Wiggy Contact` already deletes those faces before contact evaluation, so the
feature reuses the solver's own exclusion path and never touches the collider mesh.

A mask addresses faces by index, so it can go stale: adding, removing or reordering faces makes
the same index refer to different geometry. Three independent guards cover that:

* the node group marks faces only when the mask has exactly one entry per face, so a mask from
  a different face count marks nothing at all;
* a stored topology signature records the exact mesh: the four domain sizes plus every corner's
  vertex index and every face's corner count, in order. A same-count swap of two faces, or a
  change of one face's connectivity, changes it, so it is a complete check and not a sample. It
  is verified in `depsgraph_update_pre`, before the evaluation that would apply the mask, and a
  mask that no longer matches is muted in the modifier stack;
* anything that cannot be verified fails closed: a missing or unreadable record, a record from
  the older sampled format, or an exception while checking all leave the filter disabled.

The suite also marks from a live Edit Mode BMesh selection, which is how the operator is used.

The module is imported from source and registered here, so the run needs no installed add-on.
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
SHEET_ATTR = "wiggy_sheet_back"

SPEC = importlib.util.spec_from_file_location("jiggle_under_test", SOURCE)
g = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g)

failures = []
timings = {}


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + (("  <- " + str(detail)) if detail else ""))
    if not condition:
        failures.append(name)


def section(title):
    print("\n# " + title)


def update():
    bpy.context.view_layer.update()


def call(operator, **kwargs):
    """Run an operator, turning a refusal report into CANCELLED instead of an exception."""
    try:
        return set(operator(**kwargs))
    except RuntimeError:
        return {'CANCELLED'}


def mark():
    return call(bpy.ops.jiggle.mark_back_faces)


def clear():
    return call(bpy.ops.jiggle.clear_back_faces)


def activate(obj):
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def make_grid(name, subdiv=6):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdiv, y_subdivisions=subdiv, size=2.0)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def add_collider(obj):
    mod = obj.modifiers.new(name="Collider", type='NODES')
    mod.node_group = bpy.data.node_groups["Collider"]
    return mod


def make_collider(name, subdiv=6):
    obj = make_grid(name, subdiv)
    mod = add_collider(obj)
    update()
    return obj, mod


def select_faces(obj, indices):
    wanted = set(indices)
    for index, poly in enumerate(obj.data.polygons):
        poly.select = index in wanted


def selected_bits(obj):
    return "".join("1" if poly.select else "0" for poly in obj.data.polygons)


def sheet_bits(obj):
    """The face flags the solver sees, read through the real Collider modifier."""
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    attr = evaluated.data.attributes.get(SHEET_ATTR)
    if attr is None:
        return None
    return "".join("1" if bool(item.value) else "0" for item in attr.data)


def back_mod(obj):
    return g.get_back_face_modifier(obj)


def mask_bits(obj):
    return g.back_face_mask_bits(g.get_back_face_mask(back_mod(obj)))


def bits_of(text):
    return [char == "1" for char in text]


def stale_flag(obj):
    return obj.get(g.BACK_FACE_STALE_KEY)


def replace_faces_permuted(obj, offset=1):
    """Give obj a mesh with the same geometry and a rotated face order."""
    mesh = obj.data
    verts = [tuple(vert.co) for vert in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    rotated = faces[offset:] + faces[:offset]
    new_mesh = bpy.data.meshes.new(mesh.name + "_permuted")
    new_mesh.from_pydata(verts, [], rotated)
    new_mesh.update()
    obj.data = new_mesh
    update()
    return mesh


def zone_modifier(host, group_name, name, colliders=None, collection=None):
    mod = host.modifiers.new(name=name, type='NODES')
    mod.node_group = bpy.data.node_groups[group_name]
    if collection is not None:
        g.set_mod_socket(mod, "Socket_7", value=collection, sync_cage=False)
    for index, collider in enumerate(colliders or [], 1):
        object_socket = g.WIGGY_COLLIDER_SOCKET_PAIRS[index - 1][0]
        g.set_mod_socket(mod, object_socket, value=collider, sync_cage=False)
    return mod


bpy.ops.wm.read_homefile(use_empty=True)
g.register()
check("a clean scene leaves the per-update guard inactive", not g._BACK_FACE_ANY_MASK,
      g._BACK_FACE_ANY_MASK)

collider_group = g.ensure_nodetree("Collider")
back_group = g.ensure_nodetree("Back Faces")
wall_group = g.ensure_nodetree("Wiggy 0.2.0")
legacy_group = g.ensure_nodetree("Wiggy 0.1")

# --- asset and registration ----------------------------------------------------------------
section("asset and registration")
check("Collider group loads", collider_group is not None)
check("Back Faces group loads from its own asset",
      back_group is not None and g.ASSET_GROUP_FILES.get("Back Faces") == "BackFaces.blend",
      g.ASSET_GROUP_FILES.get("Back Faces"))
mask_socket = g.get_back_face_socket_id(back_group) if back_group else None
check("Face Mask socket resolves by name",
      mask_socket is not None
      and next(item for item in back_group.interface.items_tree
               if getattr(item, "identifier", "") == mask_socket).name == "Face Mask",
      mask_socket)
check("Face Mask socket is hidden in the modifier",
      back_group is not None
      and next(item for item in back_group.interface.items_tree
               if getattr(item, "identifier", "") == mask_socket).hide_in_modifier)
check("mark operator is registered", hasattr(bpy.ops.jiggle, "mark_back_faces"))
check("clear operator is registered", hasattr(bpy.ops.jiggle, "clear_back_faces"))

contact = bpy.data.node_groups.get("Wiggy Contact")
contact_refs = []
if contact:
    for node in contact.nodes:
        for sock in node.inputs:
            value = getattr(sock, "default_value", None)
            if isinstance(value, str) and value == SHEET_ATTR:
                contact_refs.append(node.bl_idname)
check("Wiggy Contact still deletes by wiggy_sheet_back",
      contact_refs == ["GeometryNodeInputNamedAttribute"], contact_refs)
check("Back Faces writes the attribute Wiggy Contact reads",
      any(node.bl_idname == "GeometryNodeStoreNamedAttribute"
          and node.inputs["Name"].default_value == SHEET_ATTR
          and node.data_type == 'BOOLEAN'
          and node.domain == 'FACE'
          for node in back_group.nodes))

# --- meaningful selections ----------------------------------------------------------------
section("exactness through the real Collider modifier")
plate, plate_mod = make_collider("Plate")
face_count = len(plate.data.polygons)
check("test fixture face count", face_count == 36, face_count)

scenarios = {
    "single face": [14],
    "adjacent run": [12, 13, 14, 15],
    "disconnected regions": [0, 7, 21, 35],
    "all but one interior face": [i for i in range(face_count) if i != 14],
    "all faces": list(range(face_count)),
}
for label, indices in scenarios.items():
    select_faces(plate, indices)
    expected = selected_bits(plate)
    result = mark()
    update()
    check(f"mark finishes: {label}", result == {'FINISHED'}, result)
    check(f"mask equals the selection: {label}", mask_bits(plate) == bits_of(expected))
    check(f"solver sees exactly those faces: {label}", sheet_bits(plate) == expected)

select_faces(plate, [])
result = mark()
check("mark refuses an empty selection", result == {'CANCELLED'}, result)
check("refused mark leaves the previous mask alone",
      sum(g.back_face_mask_bits(g.get_back_face_mask(back_mod(plate)))) == face_count)

select_faces(plate, [2, 3, 4])
mark()
update()

# --- modifier placement and non-destructiveness -------------------------------------------
section("placement and non-destructiveness")
names = [mod.name for mod in plate.modifiers]
check("filter sits immediately before Collider",
      names.index("Back Faces") == names.index("Collider") - 1, names)
check("mesh keeps every face and vertex",
      len(plate.data.polygons) == face_count and len(plate.data.vertices) == 49,
      (len(plate.data.polygons), len(plate.data.vertices)))
check("mesh datablock gains no solver attribute", plate.data.attributes.get(SHEET_ATTR) is None)
check("no vertex group is created", len(plate.vertex_groups) == 0, plate.vertex_groups[:])
check("Collider modifier survives marking",
      any(mod.node_group == collider_group for mod in plate.modifiers))

bpy.ops.mesh.primitive_cube_add()
cutter = bpy.context.active_object
subsurf = plate.modifiers.new("Subdivision", 'SUBSURF')
activate(plate)
mark()
names = [mod.name for mod in plate.modifiers]
check("filter is re-ordered in front of Collider on a later mark",
      names.index("Back Faces") == names.index("Collider") - 1, names)
plate.modifiers.remove(subsurf)
bpy.data.objects.remove(cutter, do_unlink=True)

# --- panel --------------------------------------------------------------------------------
section("panel")


class LayoutProbe:
    def __init__(self):
        self.labels = []
        self.operators = []

    def column(self, **_kwargs):
        return self

    def box(self):
        return self

    def row(self, **_kwargs):
        return self

    def label(self, text="", **_kwargs):
        self.labels.append(text)

    def operator(self, operator_id, **_kwargs):
        self.operators.append(operator_id)
        return SimpleNamespace()


def draw_panel(obj):
    probe = LayoutProbe()
    panel = SimpleNamespace(layout=probe)
    context = SimpleNamespace(active_object=obj, scene=bpy.context.scene)
    g.VIEW3D_PT_jiggle_back_faces.draw(panel, context)
    return probe


check("panel is registered", hasattr(bpy.types, "VIEW3D_PT_jiggle_back_faces"))
plain_panel = make_grid("PanelPlain")
check("panel poll ignores a mesh with no collider",
      not g.VIEW3D_PT_jiggle_back_faces.poll(
          SimpleNamespace(active_object=plain_panel)))
check("panel poll accepts a collider",
      g.VIEW3D_PT_jiggle_back_faces.poll(SimpleNamespace(active_object=plate)))
panel = draw_panel(plate)
check("panel exposes both operators",
      {"jiggle.mark_back_faces", "jiggle.clear_back_faces"} <= set(panel.operators),
      panel.operators)
check("panel reports how many faces are excluded",
      any("3 of 36" in text for text in panel.labels), panel.labels)
bpy.data.objects.remove(plain_panel, do_unlink=True)

# --- sharing ------------------------------------------------------------------------------
section("sharing")
# A fresh object on the same mesh: object.copy() would carry the filter over, which is
# exactly what we do not want if the exclusion lived on the mesh.
shared = bpy.data.objects.new("SharedPlate", plate.data)
bpy.context.scene.collection.objects.link(shared)
add_collider(shared)
update()
check("a second object on the same mesh has no filter", back_mod(shared) is None)
shared_bits = sheet_bits(shared)
check("a second object on the same mesh excludes nothing",
      shared_bits is None or "1" not in shared_bits, shared_bits)
check("the mesh datablock still has no solver attribute",
      plate.data.attributes.get(SHEET_ATTR) is None)
check("the marked object still excludes its own faces",
      sheet_bits(plate) == selected_bits(plate), sheet_bits(plate))
select_faces(plate, [9])
activate(plate)
mark()
update()
check("marking one object leaves the other untouched",
      sheet_bits(shared) is None or "1" not in sheet_bits(shared), sheet_bits(shared))
check("the mesh datablock stays clean after a second mark",
      plate.data.attributes.get(SHEET_ATTR) is None)

# --- zones --------------------------------------------------------------------------------
section("zones")
zone_host, _unused = make_collider("ZoneHost", subdiv=3)
collection = bpy.data.collections.new("Jiggle_Colliders_Test")
bpy.context.scene.collection.children.link(collection)
collection.objects.link(plate)
zone_new = zone_modifier(zone_host, "Wiggy 0.2.0", "Jiggle_Modern", colliders=[plate],
                          collection=collection)
zone_old = zone_modifier(zone_host, "Wiggy 0.1", "Jiggle_Legacy", collection=collection)
zones = g.get_zones_using_collider(plate)
check("both zone versions find the collider through slots and collection",
      {mod.name for mod in zones} == {"Jiggle_Modern", "Jiggle_Legacy"},
      [mod.name for mod in zones])
zone_host["_jiggle_baked_at_timestamp"] = 1000.0
zone_host["_jiggle_settings_modified_at"] = 0.0
select_faces(plate, [5])
activate(plate)
mark()
check("marking invalidates the bake of every referencing zone",
      time.time() - 5 < zone_host.get("_jiggle_settings_modified_at", 0)
      > zone_host.get("_jiggle_baked_at_timestamp", 0),
      zone_host.get("_jiggle_settings_modified_at"))

# --- refusals -----------------------------------------------------------------------------
section("refusals")
plain = make_grid("Plain")
select_faces(plain, [0])
activate(plain)
result = mark()
check("mark refuses an object without a Collider modifier", result == {'CANCELLED'}, result)
check("refused mark writes nothing", back_mod(plain) is None)

boundary, boundary_mod = make_collider("Boundary")
g.set_mod_socket(boundary_mod, "Socket_6", value=True, sync_cage=False)
select_faces(boundary, [0])
activate(boundary)
result = mark()
check("mark refuses a boundary collider", result == {'CANCELLED'}, result)
check("refused boundary mark writes nothing", back_mod(boundary) is None)
g.set_mod_socket(boundary_mod, "Socket_6", value=False, sync_cage=False)
mark()
check("the same collider can be marked once Boundary is off", back_mod(boundary) is not None)

# --- clear --------------------------------------------------------------------------------
section("clear")
activate(plate)
before = [mod.name for mod in plate.modifiers]
result = clear()
update()
names = [mod.name for mod in plate.modifiers]
check("clear finishes", result == {'FINISHED'}, result)
check("clear removes only the filter",
      [name for name in before if name != "Back Faces"] == names, (before, names))
check("Collider survives clearing", "Collider" in names)
check("the solver sees no excluded face after clearing",
      sheet_bits(plate) is None or "1" not in sheet_bits(plate), sheet_bits(plate))
check("clearing drops the topology record",
      plate.get(g.BACK_FACE_SIGNATURE_KEY) is None and stale_flag(plate) is None)
result = clear()
check("clearing twice is a no-op", result == {'CANCELLED'}, result)

# --- persistence --------------------------------------------------------------------------
section("save and reopen")
select_faces(plate, [6, 7, 8])
activate(plate)
mark()
update()
expected_bits = selected_bits(plate)
sandbox = tempfile.mkdtemp(prefix="jiggle_back_faces_")
saved = os.path.join(sandbox, "back_faces.blend")
bpy.ops.wm.save_as_mainfile(filepath=saved)
bpy.ops.wm.open_mainfile(filepath=saved)
check("loading a file with a filter activates the guard", g._BACK_FACE_ANY_MASK,
      g._BACK_FACE_ANY_MASK)
plate = bpy.data.objects["Plate"]
names = [mod.name for mod in plate.modifiers]
check("modifier order survives a save", names.index("Back Faces") < names.index("Collider"), names)
check("mask survives a save", mask_bits(plate) == bits_of(expected_bits))
check("status is ok after reopen", g.back_face_status(plate)[0] == 'ok', g.back_face_status(plate))
update()
check("solver sees the same faces after reopen", sheet_bits(plate) == expected_bits)

# --- topology change: face count ----------------------------------------------------------
section("topology change: face count")
mod = back_mod(plate)
activate(plate)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide()
bpy.ops.object.mode_set(mode='OBJECT')
update()
new_count = len(plate.data.polygons)
check("subdivide changes the face count", new_count > face_count, (face_count, new_count))
check("status reports the count change", g.back_face_status(plate)[0] == 'count_changed',
      g.back_face_status(plate))
check("the stale mask marks nothing", "1" not in (sheet_bits(plate) or "0"), sheet_bits(plate))
scene = bpy.context.scene
scene.frame_set(scene.frame_current + 1)
check("a stale mask is muted so it cannot be applied",
      not mod.show_viewport and not mod.show_render)
check("stale mask records why", stale_flag(plate) == 'count_changed', stale_flag(plate))
panel = draw_panel(plate)
check("panel explains the stale mask",
      any("face count changed" in text for text in panel.labels), panel.labels)
check("stale mask is preserved",
      len(g.back_face_mask_bits(g.get_back_face_mask(mod))) == face_count)
check("the safety pass is idempotent", g.back_face_safety_pass() == 0,
      g.back_face_safety_pass())

# --- topology change: face order ----------------------------------------------------------
section("topology change: face order")
replacement = make_grid("Reorder")
add_collider(replacement)
select_faces(replacement, [3, 4, 5])
activate(replacement)
mark()
update()
original_mesh = replacement.data
original_status = g.back_face_status(replacement)[0]
original_bits = sheet_bits(replacement)
check("a fresh mask starts ok", original_status == 'ok', original_status)
permuted_mesh = replace_faces_permuted(replacement)
status = g.back_face_status(replacement)[0]
check("a reordered mesh keeps the face count",
      len(replacement.data.polygons) == len(original_mesh.polygons),
      (len(original_mesh.polygons), len(replacement.data.polygons)))
check("reordering is detected as stale", status == 'reordered', status)
scene.frame_set(scene.frame_current + 1)
check("the stale mask marks nothing after reordering",
      "1" not in (sheet_bits(replacement) or "0"), sheet_bits(replacement))
check("reordering mutes the filter",
      not back_mod(replacement).show_viewport and not back_mod(replacement).show_render)
check("reordering records the reason", stale_flag(replacement) == 'reordered',
      stale_flag(replacement))

bpy.data.objects.remove(replacement, do_unlink=True)
replacement = make_grid("Reorder2")
add_collider(replacement)
replacement.data = original_mesh
update()
g.back_face_safety_pass()
check("restoring the original topology clears the stale state", stale_flag(replacement) is None,
      stale_flag(replacement))

# re-marking after a permutation works and matches the new face order
mesh_now = original_mesh
replacement_mesh = bpy.data.meshes.new("Reorder3")
replacement_mesh.from_pydata([tuple(vert.co) for vert in mesh_now.vertices], [],
                             [tuple(poly.vertices) for poly in mesh_now.polygons][1:] +
                             [tuple(poly.vertices) for poly in mesh_now.polygons][:1])
replacement_mesh.update()
obj3 = replacement.copy()
obj3.data = replacement_mesh
bpy.context.scene.collection.objects.link(obj3)
add_collider(obj3)
select_faces(obj3, [0, 1])
activate(obj3)
mark()
update()
check("re-marking a permuted mesh marks the new selection",
      sheet_bits(obj3) == selected_bits(obj3), (sheet_bits(obj3), selected_bits(obj3)))
check("re-marking restores an enabled filter",
      back_mod(obj3).show_viewport and stale_flag(obj3) is None)

# --- stale mask cannot reach an evaluation ------------------------------------------------
section("synchronous stale protection")
check("the pre-evaluation guard is registered",
      g.jiggle_back_face_pre_guard in bpy.app.handlers.depsgraph_update_pre)
check("the post-evaluation observer is gone",
      not any(getattr(handler, "__name__", "") == "jiggle_back_face_topology_guard"
              for handler in bpy.app.handlers.depsgraph_update_post))
check("the old UI timer is gone", not hasattr(g, "jiggle_back_face_safety_timer"))


def mesh_with_faces(obj, order):
    mesh = obj.data
    verts = [tuple(vert.co) for vert in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    new_mesh = bpy.data.meshes.new(mesh.name + "_edited")
    new_mesh.from_pydata(verts, [], [faces[index] for index in order])
    new_mesh.update()
    return new_mesh


# A raw mesh swap with no view_layer.update() call afterwards: the first depsgraph access
# is the evaluation that would apply the mask.
sync = make_grid("SyncReorder")
add_collider(sync)
select_faces(sync, [7, 8])
activate(sync)
mark()
update()
sync_before = sheet_bits(sync)
check("the synchronous fixture marks its faces", sync_before == selected_bits(sync), sync_before)
sync_count = len(sync.data.polygons)
sync.data = mesh_with_faces(sync, list(range(sync_count))[1:] + [0])
bits = sheet_bits(sync)
check("an un-ticked same-count reorder never applies the old mask",
      bits is None or "1" not in bits, bits)
check("the reorder mutes the filter before evaluation",
      not back_mod(sync).show_viewport and not back_mod(sync).show_render)
check("the reorder is recorded as the reason", stale_flag(sync) == 'reordered',
      stale_flag(sync))
check("the mask itself is preserved on a reorder",
      len(mask_bits(sync)) == sync_count, len(mask_bits(sync)))

# Same thing through a real operator that only reorders faces.
sortable = make_grid("SortReorder")
add_collider(sortable)
select_faces(sortable, [5])
activate(sortable)
mark()
update()
sort_before = sheet_bits(sortable)
sort_count = len(sortable.data.polygons)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.sort_elements(type='REVERSE', elements={'FACE'})
bpy.ops.object.mode_set(mode='OBJECT')
sort_after = sheet_bits(sortable)
check("the sort operator keeps the face count", len(sortable.data.polygons) == sort_count,
      (sort_count, len(sortable.data.polygons)))
check("a sorted mesh excludes nothing without a frame change",
      sort_after is None or "1" not in sort_after, sort_after)
check("a sorted mesh mutes the filter", not back_mod(sortable).show_viewport)
check("a sorted mesh records the reason", stale_flag(sortable) == 'reordered',
      stale_flag(sortable))

# Moving vertices is not a topology change: the mask must stay live.
movable = make_grid("MoveOnly")
add_collider(movable)
select_faces(movable, [4])
activate(movable)
mark()
update()
move_expected = sheet_bits(movable)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.transform.translate(value=(0.25, 0.0, 0.5))
bpy.ops.object.mode_set(mode='OBJECT')
check("moving vertices keeps the mask applied", sheet_bits(movable) == move_expected,
      (move_expected, sheet_bits(movable)))
check("moving vertices does not mute the filter",
      back_mod(movable).show_viewport and stale_flag(movable) is None)

# A face-count change must still fail safe with no frame change in between.
grow = make_grid("GrowCount")
add_collider(grow)
select_faces(grow, [3, 4])
activate(grow)
mark()
update()
grow_count = len(grow.data.polygons)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide()
bpy.ops.object.mode_set(mode='OBJECT')
grow_bits = sheet_bits(grow)
check("a face-count change excludes nothing without a frame change",
      grow_bits is None or "1" not in grow_bits, grow_bits)
check("a face-count change mutes the filter", not back_mod(grow).show_viewport)
check("a face-count change records the reason", stale_flag(grow) == 'count_changed',
      stale_flag(grow))


# --- exact topology verification: same counts, different faces -------------------------------
section("exact topology verification (same counts)")
# The old record sampled 16 faces, which on a 36-face grid means every second face (step 2):
# a swap between two unsampled faces, or a corner change on an unsampled face, kept the old
# record intact. Every case below has identical face, loop, vertex and edge counts.


def mesh_from_faces(obj, faces):
    verts = [tuple(vert.co) for vert in obj.data.vertices]
    new_mesh = bpy.data.meshes.new(obj.data.name + "_exact")
    new_mesh.from_pydata(verts, [], faces)
    new_mesh.update()
    return new_mesh


def domain_sizes(mesh):
    return (len(mesh.polygons), len(mesh.loops), len(mesh.vertices), len(mesh.edges))


def make_marked(name, indices, subdiv=6):
    obj = make_grid(name, subdiv)
    add_collider(obj)
    select_faces(obj, indices)
    activate(obj)
    mark()
    update()
    return obj


exact = make_marked("ExactBase", [3, 4, 5])
exact_faces = [tuple(poly.vertices) for poly in exact.data.polygons]
exact_sizes = domain_sizes(exact.data)
exact_sig = exact.get(g.BACK_FACE_SIGNATURE_KEY)
check("the fixture starts ok", g.back_face_status(exact)[0] == 'ok', g.back_face_status(exact))
check("the stored record parses", g.back_face_signature_counts(exact_sig) == exact_sizes,
      (exact_sig, exact_sizes))
check("the record is stable for an unchanged mesh",
      g.back_face_signature(exact.data) == exact_sig)

adjacent = list(exact_faces)
adjacent[1], adjacent[2] = adjacent[2], adjacent[1]
adjacent_mesh = mesh_from_faces(exact, adjacent)
check("swapping two unsampled faces keeps every count",
      domain_sizes(adjacent_mesh) == exact_sizes, (exact_sizes, domain_sizes(adjacent_mesh)))
check("swapping two unsampled faces changes the record",
      g.back_face_signature(adjacent_mesh) != exact_sig)
exact.data = adjacent_mesh
exact_bits = sheet_bits(exact)
check("swapping two unsampled faces is detected as stale",
      g.back_face_status(exact)[0] == 'reordered', g.back_face_status(exact))
check("swapping two unsampled faces excludes nothing", exact_bits is None or "1" not in exact_bits,
      exact_bits)
check("swapping two unsampled faces mutes the filter",
      not back_mod(exact).show_viewport and not back_mod(exact).show_render)

# Two non-adjacent unsampled faces (old sampling step 2 sampled 0, 2, 4, ...).
far = list(exact_faces)
far[1], far[3] = far[3], far[1]
far_mesh = mesh_from_faces(exact, far)
check("swapping two distant unsampled faces keeps every count",
      domain_sizes(far_mesh) == exact_sizes)
check("swapping two distant unsampled faces changes the record",
      g.back_face_signature(far_mesh) != g.back_face_signature(exact.data))

# Connectivity change on one face, corner count preserved: same vertices, rotated winding.
rotated = list(exact_faces)
first = rotated[1]
rotated[1] = first[1:] + first[:1]
rotated_mesh = mesh_from_faces(exact, rotated)
check("rotating one face's corners keeps every count",
      domain_sizes(rotated_mesh) == exact_sizes)
check("rotating one face's corners changes the record",
      g.back_face_signature(rotated_mesh) != g.back_face_signature(exact.data))

# A corner change that keeps the first corner and the edge set: reverse the remaining corners.
# The old record keyed on the first corner of the sampled face, so this passed unnoticed even
# on a sampled face.
swapped = list(exact_faces)
target = swapped[0]
swapped[0] = (target[0],) + tuple(reversed(target[1:]))
swapped_mesh = mesh_from_faces(exact, swapped)
check("reversing one face's other corners keeps every count",
      domain_sizes(swapped_mesh) == exact_sizes, (exact_sizes, domain_sizes(swapped_mesh)))
check("reversing one face's other corners changes the record",
      g.back_face_signature(swapped_mesh) != g.back_face_signature(exact.data))

# The live object now sees a mesh it never marked: the filter must be off.
exact.data = swapped_mesh
exact_bits = sheet_bits(exact)
check("a corner-connectivity change excludes nothing",
      exact_bits is None or "1" not in exact_bits, exact_bits)
check("a corner-connectivity change mutes the filter", not back_mod(exact).show_viewport)
check("a corner-connectivity change records the reason", stale_flag(exact) == 'reordered',
      stale_flag(exact))

# Moving vertices is still not a topology change under the exact record.
moved = g.back_face_signature(exact.data)
exact.data.vertices[0].co.x += 0.5
check("moving a vertex keeps the exact record", g.back_face_signature(exact.data) == moved)

# The previous (sampled) format is not accepted as a record any more.
legacy = "%d:%d:0.1,2.3" % (len(exact.data.polygons), len(exact.data.loops))
check("a sampled-format record is not accepted",
      g.back_face_signature_counts(legacy) is None, legacy)
check("an unreadable record is rejected", g.back_face_signature_counts("2:unreadable") is None)
bpy.data.objects.remove(exact, do_unlink=True)

# --- fail closed -----------------------------------------------------------------------------
section("fail closed")
fail = make_marked("FailClosed", [2, 3])
fail_sig = fail.get(g.BACK_FACE_SIGNATURE_KEY)
check("fail-closed fixture starts ok", g.back_face_status(fail)[0] == 'ok',
      g.back_face_status(fail))

del fail[g.BACK_FACE_SIGNATURE_KEY]
check("a missing record is unverified", g.back_face_status(fail)[0] == 'unverified',
      g.back_face_status(fail))
# Removing the record by hand does not tag the object, so run the pass the guard would run.
g.back_face_safety_pass()
update()
fail_bits = sheet_bits(fail)
check("a missing record excludes nothing", fail_bits is None or "1" not in fail_bits, fail_bits)
check("a missing record mutes the filter",
      not back_mod(fail).show_viewport and not back_mod(fail).show_render)
check("a missing record is recorded as the reason", stale_flag(fail) == 'unverified',
      stale_flag(fail))
panel = draw_panel(fail)
check("panel explains an unverified mask",
      any("no topology record" in text for text in panel.labels), panel.labels)

for label, value in (("malformed", "0:0:"),
                     ("sampled legacy", "%d:%d:0.1" % (len(fail.data.polygons),
                                                       len(fail.data.loops))),
                     ("wrong version", "1:%d:%d:%d:%d:0123456789abcdef"
                      % domain_sizes(fail.data))):
    fail[g.BACK_FACE_SIGNATURE_KEY] = value
    back_mod(fail).show_viewport = back_mod(fail).show_render = True
    check(f"a {label} record is unverified", g.back_face_status(fail)[0] == 'unverified',
          (label, g.back_face_status(fail)))
    update()
    check(f"a {label} record excludes nothing",
          (sheet_bits(fail) or "0").count("1") == 0, label)
    check(f"a {label} record mutes the filter", not back_mod(fail).show_viewport, label)

# A record that matches again re-enables the filter and clears the flag.
fail[g.BACK_FACE_SIGNATURE_KEY] = fail_sig
g.back_face_safety_pass()
update()
check("a matching record clears the fail-closed state", stale_flag(fail) is None,
      stale_flag(fail))
check("a matching record re-enables the filter", back_mod(fail).show_viewport)
check("a restored mask excludes its faces again", sheet_bits(fail) == selected_bits(fail))

# A renamed modifier is still found by its node group, not by its display name.
renamed = make_marked("RenamedFilter", [1, 2])
renamed_mod = back_mod(renamed)
renamed_mod.name = "Custom Back Filter"
check("the renamed modifier is not found by its old display name",
      renamed.modifiers.get("Back Faces") is None)
check("the renamed modifier is still found by its node group",
      back_mod(renamed) is not None and back_mod(renamed).name == renamed_mod.name)
del renamed[g.BACK_FACE_SIGNATURE_KEY]
renamed_mod.show_viewport = renamed_mod.show_render = True
g.back_face_safety_pass()
update()
check("a renamed modifier with a lost record is still muted",
      not renamed_mod.show_viewport and not renamed_mod.show_render)
check("a renamed modifier with a lost record is flagged",
      stale_flag(renamed) == 'unverified', stale_flag(renamed))
check("a renamed modifier with a lost record excludes nothing",
      (sheet_bits(renamed) or "0").count("1") == 0, sheet_bits(renamed))

# An exception while checking must not leave the filter on.
del fail[g.BACK_FACE_SIGNATURE_KEY]
g.back_face_safety_pass()
update()
original_signature = g.back_face_signature
try:
    def exploding_signature(_mesh):
        raise RuntimeError("simulated signature failure")
    g.back_face_signature = exploding_signature
    fail[g.BACK_FACE_SIGNATURE_KEY] = fail_sig
    mod = back_mod(fail)
    mod.show_viewport = mod.show_render = True
    changed = g.back_face_safety_pass()
    check("a failing topology check mutes the filter",
          not mod.show_viewport and not mod.show_render)
    check("a failing topology check is reported as changed", changed >= 1, changed)
    check("a failing topology check records unverified", stale_flag(fail) == 'unverified',
          stale_flag(fail))
    check("a failing topology check excludes nothing",
          (sheet_bits(fail) or "0").count("1") == 0, sheet_bits(fail))
finally:
    g.back_face_signature = original_signature

# The same for a failure inside the pass itself: the pre-guard's last resort mutes everything.
mod = back_mod(fail)
g.back_face_safety_pass()
update()
mod.show_viewport = mod.show_render = True
original_pass = g.back_face_safety_pass
original_gate = g._BACK_FACE_ANY_MASK
try:
    def exploding_pass(objects=None):
        raise RuntimeError("simulated pass failure")
    g.back_face_safety_pass = exploding_pass
    g._BACK_FACE_ANY_MASK = True
    g.jiggle_back_face_pre_guard(None, None)
    check("a failing safety pass mutes the filter",
          not mod.show_viewport and not mod.show_render)
finally:
    g.back_face_safety_pass = original_pass
    g._BACK_FACE_ANY_MASK = original_gate

g.back_face_safety_pass()
update()
check("recovery after a failing pass re-enables the filter", mod.show_viewport)
bpy.data.objects.remove(fail, do_unlink=True)

# --- selection read from the live Edit Mode BMesh --------------------------------------------
section("edit mode selection")
em = make_grid("EditModePlate", 5)
add_collider(em)
activate(em)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
import bmesh
bm = bmesh.from_edit_mesh(em.data)
selected_indices = {2, 7, 11, 12}
for index, face in enumerate(bm.faces):
    face.select = index in selected_indices
bmesh.update_edit_mesh(em.data)
check("the BMesh selection is live",
      sum(1 for face in bmesh.from_edit_mesh(em.data).faces if face.select)
      == len(selected_indices))
result = mark()
check("mark finishes while still in Edit Mode", result == {'FINISHED'}, result)
check("mark is still in Edit Mode", em.mode == 'EDIT', em.mode)
em_mask = mask_bits(em)
check("the mask has one entry per face", len(em_mask) == len(em.data.polygons),
      (len(em_mask), len(em.data.polygons)))
check("the mask equals the BMesh selection",
      em_mask == [index in selected_indices for index in range(len(em_mask))], em_mask)
check("the record matches the mesh marked in Edit Mode",
      g.back_face_status(em)[0] == 'ok', g.back_face_status(em))
bpy.ops.object.mode_set(mode='OBJECT')
update()
check("the solver sees the Edit Mode selection",
      sheet_bits(em) == "".join("1" if index in selected_indices else "0"
                                for index in range(len(em.data.polygons))),
      sheet_bits(em))

# A different selection made through Edit Mode operators, marked the same way.
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bm = bmesh.from_edit_mesh(em.data)
bm.faces.ensure_lookup_table()
for index in range(min(5, len(bm.faces))):
    bm.faces[index].select = True
bmesh.update_edit_mesh(em.data)
result = mark()
check("a second in-Edit-Mode mark finishes", result == {'FINISHED'}, result)
check("the second mask equals the new selection",
      mask_bits(em) == [index < 5 for index in range(len(em.data.polygons))], mask_bits(em))
bpy.ops.object.mode_set(mode='OBJECT')
update()
em_bits = sheet_bits(em)
check("the solver follows the second Edit Mode mark",
      em_bits is not None and em_bits[:5] == "11111" and "1" not in em_bits[5:], em_bits)

# A background session starts with undo disabled; ed.undo_push initialises it, and undo
# only has a target once a second step exists.
boundary = bpy.data.objects["Boundary"]
activate(boundary)
clear()
update()
bpy.ops.ed.undo_push(message="before mark")
select_faces(boundary, [3, 4])
activate(boundary)
mark()
update()
bpy.ops.ed.undo_push(message="marked")
marked = [char == "1" for char in selected_bits(boundary)]
check("mark is present before undo", mask_bits(boundary) == marked, mask_bits(boundary))
bpy.ops.ed.undo()
update()
boundary = bpy.data.objects["Boundary"]
after_undo = back_mod(boundary)
check("undo removes the filter",
      after_undo is None or not any(g.back_face_mask_bits(g.get_back_face_mask(after_undo))),
      after_undo is not None)
bpy.ops.ed.redo()
update()
boundary = bpy.data.objects["Boundary"]
after_redo = back_mod(boundary)
check("redo restores the filter", after_redo is not None)
check("redo restores the exact mask",
      after_redo is not None and mask_bits(boundary) == marked, mask_bits(boundary))
check("redo keeps the filter in front of Collider",
      after_redo is not None
      and [mod.name for mod in boundary.modifiers].index("Back Faces")
      == [mod.name for mod in boundary.modifiers].index("Collider") - 1,
      [mod.name for mod in boundary.modifiers])
update()
check("redo restores the excluded faces for the solver",
      sheet_bits(boundary) == "".join("1" if bit else "0" for bit in marked))
bpy.ops.ed.undo_push(message="after undo checks")

# --- linked objects -----------------------------------------------------------------------
section("linked objects")
lib_source = make_grid("LinkedSource")
add_collider(lib_source)
lib_path = os.path.join(sandbox, "linked_lib.blend")
# copy=True writes the file without making it the current one; linking from the current
# file is refused by Blender.
bpy.ops.wm.save_as_mainfile(filepath=lib_path, copy=True)
bpy.data.objects.remove(lib_source, do_unlink=True)
with bpy.data.libraries.load(lib_path, link=True) as (src, dst):
    dst.objects = [name for name in src.objects if name == "LinkedSource"]
linked = dst.objects[0]
check("linked fixture loads", linked is not None)
if linked is not None:
    bpy.context.scene.collection.objects.link(linked)
    activate(linked)
    before = [mod.name for mod in linked.modifiers]
    result = mark()
    check("mark refuses a linked object", result == {'CANCELLED'}, result)
    check("refused linked mark writes nothing",
          [mod.name for mod in linked.modifiers] == before,
          [mod.name for mod in linked.modifiers])
    # The same object must work once it is local, so the refusal was about the link.
    bpy.ops.object.make_local(type='SELECT_OBJECT')
    linked = bpy.data.objects["LinkedSource"]
    select_faces(linked, [0])
    activate(linked)
    result = mark()
    check("the same object can be marked after making it local",
          result == {'FINISHED'}, result)
    check("marking the now-local object writes the filter", back_mod(linked) is not None)
else:
    check("linked fixture could be created", False, lib_source.name)

# --- performance --------------------------------------------------------------------------
section("performance")
bpy.ops.mesh.primitive_grid_add(x_subdivisions=100, y_subdivisions=100, size=4.0)
big = bpy.context.active_object
big.name = "BigPlate"
add_collider(big)
select_faces(big, [i for i in range(len(big.data.polygons)) if i % 97 == 13])
activate(big)
update()
start = time.perf_counter()
mark()
timings["mark_10k"] = (time.perf_counter() - start) * 1000
start = time.perf_counter()
for _ in range(20):
    g.back_face_status(big)
timings["status_10k"] = (time.perf_counter() - start) * 1000 / 20
start = time.perf_counter()
g.back_face_signature(big.data)
timings["signature_10k"] = (time.perf_counter() - start) * 1000
back = back_mod(big)
back.show_viewport = False
update()
back.show_viewport = True
start = time.perf_counter()
update()
timings["evaluate_10k"] = (time.perf_counter() - start) * 1000
check("10k face collider is excluded exactly",
      sheet_bits(big) == selected_bits(big))
print("TIMING " + ", ".join(f"{key}={value:.2f}ms" for key, value in timings.items()))

# --- lazy guard on load ----------------------------------------------------------------------
section("lazy guard initialization")
clean_path = os.path.join(sandbox, "clean_scene.blend")
bpy.ops.wm.read_homefile(use_empty=True)
check("reloading a clean scene keeps the guard inactive", not g._BACK_FACE_ANY_MASK,
      g._BACK_FACE_ANY_MASK)
bpy.ops.wm.save_as_mainfile(filepath=clean_path)
bpy.ops.wm.open_mainfile(filepath=clean_path)
check("loading a saved clean scene keeps the guard inactive", not g._BACK_FACE_ANY_MASK,
      g._BACK_FACE_ANY_MASK)
bpy.ops.wm.open_mainfile(filepath=saved)
check("loading the saved filtered scene activates the guard", g._BACK_FACE_ANY_MASK,
      g._BACK_FACE_ANY_MASK)

# --- summary ------------------------------------------------------------------------------
print()
print("RESULT", "PASS" if not failures else f"FAIL ({len(failures)} checks)")
for name in failures:
    print("  failed:", name)
sys.stdout.flush()
raise SystemExit(0 if not failures else 1)
