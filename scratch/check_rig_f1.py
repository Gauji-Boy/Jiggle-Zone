import bpy

rig = bpy.data.objects.get("Kasumi_rig")
act = rig.animation_data.action

print("Inspecting Kasumi_rig action channels at frame 0, 1, 2:")
# Let's inspect fcurves or slot
if hasattr(act, 'fcurves'):
    for fc in act.fcurves[:10]:
        print(f"FCurve: {fc.data_path}[{fc.array_index}]")
        k_f1 = [kp.co[1] for kp in fc.keyframe_points if int(kp.co[0]) == 1]
        k_f2 = [kp.co[1] for kp in fc.keyframe_points if int(kp.co[0]) == 2]
        print(f"  Frame 1 val: {k_f1}, Frame 2 val: {k_f2}")

# Now let's check bone position at frame 1 and 2 directly on the rig
b = rig.pose.bones.get("c_breast_01.l")
bpy.context.scene.frame_set(1)
print(f"Rig Frame 1: c_breast_01.l head={rig.matrix_world @ b.head}")
bpy.context.scene.frame_set(2)
print(f"Rig Frame 2: c_breast_01.l head={rig.matrix_world @ b.head}")

# What about the root bone?
c_root = rig.pose.bones.get("c_root.x") or rig.pose.bones.get("root.x")
if c_root:
    bpy.context.scene.frame_set(1)
    print(f"Root Frame 1: {c_root.location}")
    bpy.context.scene.frame_set(2)
    print(f"Root Frame 2: {c_root.location}")
