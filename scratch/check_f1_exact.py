import bpy

body = bpy.data.objects.get("kasumi_body")
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)

print("Body vert 791 on frame 1:")
print("Evaluated co:", b_eval.matrix_world @ b_eval.data.vertices[791].co)
print("Mesh data co (rest):", body.matrix_world @ body.data.vertices[791].co)

for m in body.modifiers:
    print(f"Mod {m.name} ({m.type}), show_viewport={m.show_viewport}")
