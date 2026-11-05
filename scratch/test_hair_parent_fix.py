import bpy

hair = bpy.data.objects.get('hair')
body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')

print("Before fix:")
print("  hair.parent:", hair.parent)
print("  hair.location:", hair.location)
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_z = max(v.co.z for v in body.evaluated_get(dg).data.vertices)
h_z = max(v.co.z for v in hair.evaluated_get(dg).data.vertices)
print(f"  Frame 1: body_z={b_z:.3f}, hair_z={h_z:.3f}, diff={h_z - b_z:.3f}")

# Apply fix:
hair.parent = rig
hair.matrix_parent_inverse = rig.matrix_world.inverted()
hair.location = (0, 0, 0)
hair.rotation_euler = (0, 0, 0)
hair.scale = (1, 1, 1)

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_z = max(v.co.z for v in body.evaluated_get(dg).data.vertices)
h_z = max(v.co.z for v in hair.evaluated_get(dg).data.vertices)
print("After fix:")
print(f"  Frame 1: body_z={b_z:.3f}, hair_z={h_z:.3f}, diff={h_z - b_z:.3f}")
