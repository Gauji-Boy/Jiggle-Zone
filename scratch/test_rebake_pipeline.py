import bpy
import os
import sys
import time
import json
import hashlib

sys.path.append(r'd:\Blender\Giggle\scratch')
from test_fingerprint_eval import (
    compute_animation_hash,
    compute_armature_hash,
    compute_physics_hash,
    compute_geometry_hash,
    compute_simulation_hash,
    get_action_fcurves
)

def get_driving_armature(cage_or_mesh):
    if not cage_or_mesh:
        return None
    for m in getattr(cage_or_mesh, "modifiers", []):
        if m.type == 'ARMATURE' and m.object:
            return m.object
    if cage_or_mesh.parent and getattr(cage_or_mesh.parent, "type", "") == 'ARMATURE':
        return cage_or_mesh.parent
    src_body_name = cage_or_mesh.get('_giggle_source_body')
    if src_body_name:
        src_body = bpy.data.objects.get(src_body_name)
        if src_body:
            for m in getattr(src_body, "modifiers", []):
                if m.type == 'ARMATURE' and m.object:
                    return m.object
            if src_body.parent and getattr(src_body.parent, "type", "") == 'ARMATURE':
                return src_body.parent
    for o in bpy.data.objects:
        if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action:
            return o
    return None

def compute_zone_fingerprint(cage_or_mesh, context, storage_mode="PACKED", f_start=1, f_end=100):
    scene = context.scene
    arm = get_driving_armature(cage_or_mesh)
    return {
        "schema": "2.0.0",
        "animation": compute_animation_hash(arm),
        "armature": compute_armature_hash(arm),
        "physics": compute_physics_hash(cage_or_mesh),
        "geometry": compute_geometry_hash(cage_or_mesh),
        "simulation": compute_simulation_hash(scene, None, storage_mode, f_start, f_end)
    }

def check_cage_validity(cage_obj, context):
    if not cage_obj or cage_obj.type != 'MESH':
        return 'NOT_BAKED', "Object is not a mesh"
    
    bake_time = cage_obj.get('_giggle_baked_at_timestamp', None)
    if not bake_time:
        return 'NOT_BAKED', "Not baked"
    
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod or not mod.bakes:
        return 'NOT_BAKED', "Missing Wiggy modifier or bake items"
    
    has_data = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_data:
        return 'NOT_BAKED', "No simulation cache blocks present"
    
    fp_json = cage_obj.get('_giggle_bake_fingerprint_json', None)
    if not fp_json:
        # Check UI slider modification timestamp
        if cage_obj.get('_giggle_settings_modified_at', 0) > bake_time:
            return 'OUTDATED', "Physics settings modified"
        return 'OUTDATED', "Missing dependency fingerprint (baked with older version)"
    
    try:
        saved_fp = json.loads(fp_json)
    except Exception:
        return 'OUTDATED', "Invalid fingerprint format"
    
    # Compute current fingerprint
    frange = cage_obj.get('_giggle_baked_frame_range', (context.scene.frame_start, context.scene.frame_end))
    storage = cage_obj.get('_giggle_baked_storage', 'PACKED')
    curr_fp = compute_zone_fingerprint(cage_obj, context, storage, frange[0], frange[1])
    
    if saved_fp.get('animation') != curr_fp['animation']:
        return 'OUTDATED', "Animation keyframes or handles modified"
    if saved_fp.get('physics') != curr_fp['physics']:
        return 'OUTDATED', "Physics settings modified"
    if saved_fp.get('geometry') != curr_fp['geometry']:
        return 'OUTDATED', "Cage geometry or vertex weights modified"
    if saved_fp.get('armature') != curr_fp['armature']:
        return 'OUTDATED', "Armature rest pose or rig constraints modified"
    if saved_fp.get('simulation') != curr_fp['simulation']:
        return 'OUTDATED', "Frame range, FPS, or storage mode modified"
        
    return 'BAKED', "Cache matches setup"

# Test simulation pipeline execution
context = bpy.context
cage = bpy.data.objects.get("Chest_Cage")
print("Target cage:", cage.name)

# 1. Clear cache
with context.temp_override(active_object=cage, selected_objects=[cage]):
    del_res = bpy.ops.object.simulation_nodes_cache_delete(selected=True)
print("Delete result:", del_res)

# 2. Check validity before bake
status, reason = check_cage_validity(cage, context)
print("Status after clear:", status, f"({reason})")
assert status == 'NOT_BAKED'

# 3. Bake individually
f_start = 1
f_end = 25 # Short range for rapid testing
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

print("Bake result:", bake_res)
assert bake_res == {'FINISHED'}

# 4. Verify data blocks
mod = next(m for m in cage.modifiers if m.type == 'NODES' and m.node_group.name == 'Wiggy 0.1')
has_blocks = any(len(b.data_blocks) > 0 for b in mod.bakes)
print("Has data blocks?", has_blocks)
assert has_blocks

# 5. Commit fingerprint
fp = compute_zone_fingerprint(cage, context, storage_mode, f_start, f_end)
cage['_giggle_baked_at_timestamp'] = time.time()
cage['_giggle_bake_fingerprint_json'] = json.dumps(fp, sort_keys=True)
cage['_giggle_bake_schema_version'] = "2.0.0"
cage['_giggle_baked_frame_range'] = (f_start, f_end)
cage['_giggle_baked_storage'] = storage_mode
cage['_giggle_status'] = "BAKED"
cage['_giggle_last_known_valid'] = True
cage['_giggle_outdated_reason'] = ""

# 6. Verify status immediately after commit
status, reason = check_cage_validity(cage, context)
print("Status immediately after bake:", status, f"({reason})")
assert status == 'BAKED'

# 7. Invalidate via animation edit
arm = get_driving_armature(cage)
act = arm.animation_data.action
fc = get_action_fcurves(act)[0]
orig_y = fc.keyframe_points[0].co[1]
fc.keyframe_points[0].co[1] += 0.1

status_anim, reason_anim = check_cage_validity(cage, context)
print("Status after keyframe change:", status_anim, f"({reason_anim})")
assert status_anim == 'OUTDATED'
assert "Animation" in reason_anim

# Revert keyframe
fc.keyframe_points[0].co[1] = orig_y
status_restored, reason_restored = check_cage_validity(cage, context)
print("Status after keyframe revert:", status_restored, f"({reason_restored})")
assert status_restored == 'BAKED'

print("\nPIPELINE VERIFICATION SUCCESSFUL!")
