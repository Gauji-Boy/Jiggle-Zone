import bpy

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")
wiggy_mod = body.modifiers.get("Giggle_Jiggle_Zone")

print("Stepping sequentially frame 1 to 10...")
bpy.context.scene.frame_set(1)

# Check vertices 500..520 (in breast zone)
vg = body.vertex_groups.get("Jiggle_Zone")
vg_idx = vg.index
breast_verts = [v.index for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.8 for g in v.groups)]
print(f"Tracking {len(breast_verts)} breast verts...")

for f in range(1, 11):
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(dg)
    
    # Check evaluated position of a breast vert vs base mesh
    pt = b_eval.matrix_world @ b_eval.data.vertices[breast_verts[0]].co
    print(f"Frame {f:2d}: breast vert[0] pos={pt}")
