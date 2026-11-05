import bpy

rig = bpy.data.objects.get('Kasumi_rig')
bpy.context.scene.frame_set(1)

print("=== KASUMI_RIG POSE AT FRAME 1 ===")
for pb in rig.pose.bones:
    if any(k in pb.name.lower() for k in ['arm', 'forearm', 'hand', 'thigh', 'leg', 'foot', 'spine']):
        # if rotated or translated away from identity
        if pb.rotation_euler != (0,0,0) or (pb.rotation_quaternion and tuple(round(x, 2) for x in pb.rotation_quaternion) != (1.0, 0.0, 0.0, 0.0)) or pb.location != (0,0,0):
            print(f"  {pb.name}: loc={pb.location}, rot_e={pb.rotation_euler}, rot_q={pb.rotation_quaternion}")
