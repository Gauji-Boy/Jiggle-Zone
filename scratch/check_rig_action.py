import bpy

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')

print("Rig animation data:", rig.animation_data)
if rig.animation_data and rig.animation_data.action:
    act = rig.animation_data.action
    print(f"Action: {act.name}, range: {act.frame_range}")
    # Check if there are keyframes at frame 1
    f1_keys = []
    for fcu in act.fcurves:
        for kp in fcu.keyframe_points:
            if abs(kp.co.x - 1.0) < 0.001:
                f1_keys.append((fcu.data_path, fcu.array_index, kp.co.y))
    print(f"Keyframes at frame 1: {len(f1_keys)}")
    if len(f1_keys) > 0:
        print("Sample keyframe at f1:", f1_keys[0])

# Now check Kasumi_grp_rig or other rigs in scene:
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print(f"Armature '{o.name}': anim_data={o.animation_data is not None}")
        if o.animation_data and o.animation_data.action:
            print(f"  Action: {o.animation_data.action.name}, range: {o.animation_data.action.frame_range}")
