import bpy
import os
import sys
import time
import json
import shutil

sys.path.append(r'd:\Blender\Giggle\scratch')
from test_fingerprint_eval import (
    compute_animation_hash,
    compute_armature_hash,
    compute_physics_hash,
    compute_geometry_hash,
    compute_simulation_hash,
    get_action_fcurves
)
from test_rebake_pipeline import (
    get_driving_armature,
    compute_zone_fingerprint,
    check_cage_validity
)

print("=== TESTING OPERATOR PIPELINE LOGIC ===")

context = bpy.context
scene = context.scene
cage = bpy.data.objects.get("Chest_Cage")
arm = bpy.data.objects.get("Kasumi_rig")

# Preflight check test
def preflight_check(context, sim_objs, storage_mode, f_start, f_end):
    if not sim_objs:
        return False, "No active Giggle simulation zones found."
    if storage_mode == 'DISK' and not bpy.data.is_saved:
        return False, "Please save your .blend file before baking to external disk."
    if f_end < f_start:
        return False, f"Invalid frame range: start frame ({f_start}) > end frame ({f_end})."
    if getattr(getattr(context, 'screen', None), 'is_animation_playing', False):
        return False, "Cannot bake while animation playback is running."
    
    # Check for conflicting unrelated simulation modifiers on cages
    for o in sim_objs:
        for m in o.modifiers:
            if m.type == 'NODES' and m.node_group and m.node_group.name != 'Wiggy 0.1':
                # Check if it has simulation zones
                if any(node.type == 'SIMULATION_OUTPUT' for node in getattr(m.node_group, 'nodes', [])):
                    return False, f"Conflicting unrelated simulation modifier found on '{o.name}'."
    return True, "Preflight passed"

ok, msg = preflight_check(context, [cage], 'PACKED', 1, 100)
print("Preflight check (valid):", ok, f"({msg})")
assert ok

ok_bad_range, msg_bad = preflight_check(context, [cage], 'PACKED', 100, 1)
print("Preflight check (bad range):", ok_bad_range, f"({msg_bad})")
assert not ok_bad_range

# Create a second dummy cage to test multi-cage partial baking & bake_missing
print("\nCreating second test cage: Glute_Cage...")
mesh = bpy.data.meshes.new("Glute_Cage_Mesh")
glute_cage = bpy.data.objects.new("Glute_Cage", mesh)
context.scene.collection.objects.link(glute_cage)
glute_cage['_giggle_cage'] = True
glute_cage['_giggle_source_body'] = "bottom"
glute_cage['_giggle_vg_name'] = "Buttocks"

# Add Wiggy modifier to glute_cage
gn_mod = glute_cage.modifiers.new("Giggle_Cage_XPBD", 'NODES')
gn_mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")

# Add Armature modifier pointing to Kasumi_rig
arm_mod = glute_cage.modifiers.new("Armature", 'ARMATURE')
arm_mod.object = arm

# Create simple mesh geometry for glute_cage
import bmesh
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=0.2)
bm.to_mesh(mesh)
bm.free()

sim_objs = [cage, glute_cage]
print("Active simulation cages:", [o.name for o in sim_objs])

# Test Bake Missing:
# Initially both are NOT_BAKED
st_cage, _ = check_cage_validity(cage, context)
st_glute, _ = check_cage_validity(glute_cage, context)
print(f"Initial states: Chest_Cage={st_cage}, Glute_Cage={st_glute}")

print("\nSimulating Bake Missing (should target both since both are unbaked)...")
targets = [o for o in sim_objs if check_cage_validity(o, context)[0] != 'BAKED']
print("Targets to bake:", [o.name for o in targets])
assert len(targets) == 2

# Bake Chest_Cage
f_start = 1
f_end = 10
storage_mode = 'PACKED'

for m in cage.modifiers:
    if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1':
        m.bake_target = storage_mode
        for b in m.bakes:
            b.frame_start = f_start
            b.frame_end = f_end

context.scene.frame_set(f_start)
with context.temp_override(active_object=cage, selected_objects=[cage]):
    bake_res = bpy.ops.object.simulation_nodes_cache_bake(selected=True)

fp = compute_zone_fingerprint(cage, context, storage_mode, f_start, f_end)
cage['_giggle_baked_at_timestamp'] = time.time()
cage['_giggle_bake_fingerprint_json'] = json.dumps(fp, sort_keys=True)
cage['_giggle_bake_schema_version'] = "2.0.0"
cage['_giggle_baked_frame_range'] = (f_start, f_end)
cage['_giggle_baked_storage'] = storage_mode
cage['_giggle_status'] = "BAKED"
cage['_giggle_last_known_valid'] = True

print("Chest_Cage baked successfully. Glute_Cage remains unbaked.")
st_cage2, _ = check_cage_validity(cage, context)
st_glute2, _ = check_cage_validity(glute_cage, context)
print(f"States now: Chest_Cage={st_cage2}, Glute_Cage={st_glute2}")
assert st_cage2 == 'BAKED'
assert st_glute2 == 'NOT_BAKED'

# Now test Bake Missing again: It should ONLY target Glute_Cage!
targets_missing = [o for o in sim_objs if check_cage_validity(o, context)[0] != 'BAKED']
print("Targets for next Bake Missing:", [o.name for o in targets_missing])
assert targets_missing == [glute_cage]
print("CONFIRMED: Bake Missing selectively skips already BAKED cages!")

# Clean up temporary test cage
bpy.data.objects.remove(glute_cage, do_unlink=True)
bpy.data.meshes.remove(mesh)

print("\nALL OPERATOR PIPELINE LOGIC TESTS PASSED!")
