import bpy

hair = bpy.data.objects.get('hair')
body = bpy.data.objects.get('kasumi_body')

print("Before apply transforms on hair:")
print("  hair location:", hair.location)
print("  hair matrix_world:", hair.matrix_world.translation)

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_z = max(v.co.z for v in body.evaluated_get(dg).data.vertices)
h_z = max(v.co.z for v in hair.evaluated_get(dg).data.vertices)
print(f"  Frame 1: body_z={b_z:.3f}, hair_z={h_z:.3f}, diff={h_z - b_z:.3f}")

# Check hair vertex groups
vgs = [vg.name for vg in hair.vertex_groups]
print("Hair vertex groups count:", len(vgs), "Has c_head.x:", 'c_head.x' in vgs, "Has head.x:", 'head.x' in vgs)
