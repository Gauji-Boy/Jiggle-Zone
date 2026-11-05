import bpy

topcen = bpy.data.objects.get("topcen")
body = bpy.data.objects.get("kasumi_body")

print("Inspecting topcen at Frame 1:")
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()

tc_eval = topcen.evaluated_get(dg)
b_eval = body.evaluated_get(dg)

print(f"topcen has {len(tc_eval.data.vertices)} verts")
print(f"topcen modifiers:")
for m in topcen.modifiers:
    print(f"  {m.name} ({m.type})")

# Check bounding box of topcen vs kasumi_body
tc_pts = [tc_eval.matrix_world @ v.co for v in tc_eval.data.vertices]
b_pts = [b_eval.matrix_world @ v.co for v in b_eval.data.vertices]

min_tc = [min(p[i] for p in tc_pts) for i in range(3)]
max_tc = [max(p[i] for p in tc_pts) for i in range(3)]
print(f"topcen bounding box Z: {min_tc[2]:.3f} to {max_tc[2]:.3f}")

# Check top bounding box Z
top = bpy.data.objects.get("top")
t_eval = top.evaluated_get(dg)
t_pts = [t_eval.matrix_world @ v.co for v in t_eval.data.vertices]
min_t = [min(p[i] for p in t_pts) for i in range(3)]
max_t = [max(p[i] for p in t_pts) for i in range(3)]
print(f"top bounding box Z:    {min_t[2]:.3f} to {max_t[2]:.3f}")
