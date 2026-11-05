import bpy

arm = bpy.data.objects.get('Armature')
bpy.context.scene.frame_set(1)
print("=== ARMATURE POSE BONES AT FRAME 1 ===")
for pb in arm.pose.bones:
    if any(k in pb.name.lower() for k in ['arm', 'hand', 'leg', 'foot', 'hip']):
        rot = pb.rotation_quaternion or pb.rotation_euler
        print(f"  {pb.name}: loc={pb.location}, rot={rot}")
