import bpy
import hashlib
import json

def get_action_fcurves(act):
    """Retrieve all F-Curves from an action, supporting both Blender 5.2/5.3 Layered Actions and legacy actions."""
    if not act:
        return []
    fcurves = []
    # Blender 5.2+ Layered Actions (Animation 2025)
    if hasattr(act, "layers") and act.layers:
        for layer in act.layers:
            for strip in getattr(layer, "strips", []):
                for cb in getattr(strip, "channelbags", []):
                    fcurves.extend(cb.fcurves)
    # Legacy Action fallback
    elif hasattr(act, "fcurves") and act.fcurves:
        fcurves.extend(act.fcurves)
    return fcurves

def compute_animation_hash(arm_obj):
    """Deterministic hash of armature animation keyframes, handles, and interpolation."""
    if not arm_obj or not arm_obj.animation_data:
        return "NO_ANIM"
    
    act = arm_obj.animation_data.action
    if not act:
        return "NO_ACTION"
    
    fcurves = get_action_fcurves(act)
    if not fcurves:
        return f"EMPTY_ACTION_{act.name}"
    
    h = hashlib.sha256()
    h.update(act.name.encode('utf-8'))
    
    # Sort fcurves by data_path and array_index for deterministic ordering
    sorted_fc = sorted(fcurves, key=lambda fc: (fc.data_path, fc.array_index))
    for fc in sorted_fc:
        h.update(f"{fc.data_path}[{fc.array_index}]".encode('utf-8'))
        for kp in fc.keyframe_points:
            # Round coordinates to avoid floating point precision differences
            entry = f"{round(kp.co[0], 3)}:{round(kp.co[1], 4)}:{round(kp.handle_left[0], 3)}:{round(kp.handle_left[1], 4)}:{round(kp.handle_right[0], 3)}:{round(kp.handle_right[1], 4)}:{kp.interpolation};"
            h.update(entry.encode('utf-8'))
            
    return h.hexdigest()

def compute_armature_hash(arm_obj):
    """Deterministic hash of armature bone rest transforms and constraints."""
    if not arm_obj or arm_obj.type != 'ARMATURE' or not arm_obj.data:
        return "NO_ARMATURE"
    h = hashlib.sha256()
    for b in sorted(arm_obj.data.bones, key=lambda x: x.name):
        h.update(b.name.encode('utf-8'))
        h.update(f"{b.head.x:.4f},{b.head.y:.4f},{b.head.z:.4f}".encode('utf-8'))
        h.update(f"{b.tail.x:.4f},{b.tail.y:.4f},{b.tail.z:.4f}".encode('utf-8'))
    # Also pose bone constraints
    if arm_obj.pose:
        for pb in sorted(arm_obj.pose.bones, key=lambda x: x.name):
            for c in pb.constraints:
                h.update(f"{pb.name}:{c.type}:{c.mute}:{getattr(c, 'influence', 1.0):.4f}".encode('utf-8'))
    return h.hexdigest()

def compute_physics_hash(cage_obj):
    """Deterministic hash of Giggle Wiggy GN modifier inputs."""
    if not cage_obj:
        return "NO_OBJ"
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod:
        return "NO_WIGGY_MOD"
    
    h = hashlib.sha256()
    s_in = getattr(getattr(mod, "properties", None), "inputs", None)
    if s_in:
        for identifier in sorted(dir(s_in)):
            if identifier.startswith("Socket_"):
                sock = getattr(s_in, identifier)
                val = getattr(sock, "value", None)
                if val is not None:
                    h.update(f"{identifier}={val};".encode('utf-8'))
                att = getattr(sock, "attribute_name", None)
                if att is not None:
                    h.update(f"{identifier}_att={att};".encode('utf-8'))
    return h.hexdigest()

def compute_geometry_hash(cage_obj):
    """Deterministic hash of cage mesh vertex count and rest vertex coordinates."""
    if not cage_obj or cage_obj.type != 'MESH' or not cage_obj.data:
        return "NO_GEOMETRY"
    h = hashlib.sha256()
    mesh = cage_obj.data
    h.update(f"vcount={len(mesh.vertices)};".encode('utf-8'))
    for v in mesh.vertices:
        h.update(f"{v.co.x:.4f},{v.co.y:.4f},{v.co.z:.4f};".encode('utf-8'))
    return h.hexdigest()

def compute_simulation_hash(scene, settings, storage_mode, f_start, f_end):
    """Deterministic hash of scene frame range, FPS, and storage mode."""
    h = hashlib.sha256()
    fps = round(scene.render.fps / scene.render.fps_base, 3)
    h.update(f"range={f_start}-{f_end};fps={fps};storage={storage_mode};".encode('utf-8'))
    return h.hexdigest()

# Test run
cage = bpy.data.objects.get("Chest_Cage")
arm = bpy.data.objects.get("Kasumi_rig")
scene = bpy.context.scene

print("Testing Fingerprint on Chest_Cage:")
anim_hash = compute_animation_hash(arm)
arm_hash = compute_armature_hash(arm)
phys_hash = compute_physics_hash(cage)
geom_hash = compute_geometry_hash(cage)
sim_hash = compute_simulation_hash(scene, None, "PACKED", 1, 100)

print("  Animation Hash:", anim_hash[:16])
print("  Armature Hash: ", arm_hash[:16])
print("  Physics Hash:  ", phys_hash[:16])
print("  Geometry Hash: ", geom_hash[:16])
print("  Simulation Hash:", sim_hash[:16])

fingerprint = {
    "schema": "2.0.0",
    "animation": anim_hash,
    "armature": arm_hash,
    "physics": phys_hash,
    "geometry": geom_hash,
    "simulation": sim_hash,
}
full_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode('utf-8')).hexdigest()
print("  Combined Hash: ", full_hash)
