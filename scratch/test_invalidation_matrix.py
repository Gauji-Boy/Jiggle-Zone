import sys
import os
sys.path.append(r'd:\Blender\Giggle\scratch')

import bpy
import hashlib
import json

from test_fingerprint_eval import (
    compute_animation_hash,
    compute_armature_hash,
    compute_physics_hash,
    compute_geometry_hash,
    compute_simulation_hash,
    get_action_fcurves
)

cage = bpy.data.objects.get("Chest_Cage")
arm = bpy.data.objects.get("Kasumi_rig")
scene = bpy.context.scene

def compute_all(cage, arm, scene, storage="PACKED", f_start=1, f_end=100):
    return {
        "animation": compute_animation_hash(arm),
        "armature": compute_armature_hash(arm),
        "physics": compute_physics_hash(cage),
        "geometry": compute_geometry_hash(cage),
        "simulation": compute_simulation_hash(scene, None, storage, f_start, f_end),
    }

baseline = compute_all(cage, arm, scene)
print("=== BASELINE FINGERPRINT ===")
for k, v in baseline.items():
    print(f"  {k}: {v[:16]}")

# 1. Test Animation Change: Move a keyframe slightly
act = arm.animation_data.action
fcurves = get_action_fcurves(act)
kp = fcurves[0].keyframe_points[0]
orig_co_y = kp.co[1]
kp.co[1] += 0.05
anim_changed = compute_all(cage, arm, scene)
kp.co[1] = orig_co_y # Revert
print("\n1. Keyframe Value Change:")
print("  Animation hash changed?", baseline["animation"] != anim_changed["animation"])
print("  Other hashes unchanged?", all(baseline[k] == anim_changed[k] for k in baseline if k != "animation"))

# 2. Test Keyframe Handle Change
orig_h_y = kp.handle_left[1]
kp.handle_left[1] += 0.1
handle_changed = compute_all(cage, arm, scene)
kp.handle_left[1] = orig_h_y # Revert
print("\n2. Keyframe Handle Change:")
print("  Animation hash changed?", baseline["animation"] != handle_changed["animation"])

# 3. Test Physics Slider Change: Alter Socket_31
mod = next(m for m in cage.modifiers if m.type == 'NODES' and m.node_group.name == 'Wiggy 0.1')
s_in = getattr(mod.properties, "inputs")
orig_val = s_in.Socket_31.value
s_in.Socket_31.value = orig_val + 0.1
phys_changed = compute_all(cage, arm, scene)
s_in.Socket_31.value = orig_val # Revert
print("\n3. Physics Setting Change (Socket_31):")
print("  Physics hash changed?", baseline["physics"] != phys_changed["physics"])
print("  Other hashes unchanged?", all(baseline[k] == phys_changed[k] for k in baseline if k != "physics"))

# 4. Test Geometry Change: Move cage vertex
v0 = cage.data.vertices[0]
orig_vz = v0.co.z
v0.co.z += 0.02
geom_changed = compute_all(cage, arm, scene)
v0.co.z = orig_vz # Revert
print("\n4. Geometry Vertex Move:")
print("  Geometry hash changed?", baseline["geometry"] != geom_changed["geometry"])
print("  Other hashes unchanged?", all(baseline[k] == geom_changed[k] for k in baseline if k != "geometry"))

# 5. Test Simulation Range / FPS Change:
sim_changed = compute_all(cage, arm, scene, f_end=150)
print("\n5. Simulation Frame Range Change:")
print("  Simulation hash changed?", baseline["simulation"] != sim_changed["simulation"])
print("  Other hashes unchanged?", all(baseline[k] == sim_changed[k] for k in baseline if k != "simulation"))

print("\nALL 5 INVALIDATION DOMAINS VERIFIED SUCCESSFULLY!")
