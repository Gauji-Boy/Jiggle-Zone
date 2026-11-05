import bpy

mixamo_arm = bpy.data.objects['Armature']
kasumi_arm = bpy.data.objects['Kasumi_rig']

mixamo_act = mixamo_arm.animation_data.action
kasumi_act = kasumi_arm.animation_data.action

print(f'Mixamo action: {mixamo_act.name}, range: {mixamo_act.frame_range}')
print(f'Kasumi action: {kasumi_act.name}, range: {kasumi_act.frame_range}')

# Check arm positions at Frame 1 vs Frame 2 on Mixamo
scene = bpy.context.scene

print('\n=== MIXAMO BONES AT FRAME 1 vs 2 ===')
for f in [1, 2, 3]:
    scene.frame_set(f)
    print(f'Frame {f}:')
    for bname in ['RightArm', 'mixamorig:RightArm', 'RightForeArm', 'mixamorig:RightForeArm']:
        pb = mixamo_arm.pose.bones.get(bname)
        if pb:
            print(f'   {bname} rot_euler={pb.rotation_euler}, loc={pb.location}')

print('\n=== KASUMI BONES AT FRAME 1 vs 2 ===')
for f in [1, 2, 3]:
    scene.frame_set(f)
    print(f'Frame {f}:')
    for bname in ['c_arm_fk.r', 'c_forearm_fk.r', 'c_arm_ik.r', 'c_hand_ik.r', 'arm_fk.r']:
        pb = kasumi_arm.pose.bones.get(bname)
        if pb:
            print(f'   {bname} rot_euler={pb.rotation_euler}, loc={pb.location}')
