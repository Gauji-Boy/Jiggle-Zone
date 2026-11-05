import bpy

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

print("Checking bind behavior step by step...")
scene = bpy.context.scene
scene.frame_set(1)

# Check top and body before attach
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)
t_eval = top.evaluated_get(dg)
print("Before attach, Frame 1:")
print("  body vert 791:", b_eval.matrix_world @ b_eval.data.vertices[791].co)
print("  top vert 0:   ", t_eval.matrix_world @ t_eval.data.vertices[0].co)

# Run attach
bpy.ops.object.select_all(action='DESELECT')
top.select_set(True)
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.giggle.attach_clothing_proxy()

# Now check immediately after attach at Frame 1
scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)
t_eval = top.evaluated_get(dg)

sd = top.modifiers.get("Giggle_SurfaceDeform")
proxy = sd.target if sd else None
p_eval = proxy.evaluated_get(dg) if proxy else None

print("\nImmediately after attach, Frame 1:")
print("  body vert 791: ", b_eval.matrix_world @ b_eval.data.vertices[791].co)
print("  top vert 0:    ", t_eval.matrix_world @ t_eval.data.vertices[0].co)
print("  proxy vert 0:  ", p_eval.matrix_world @ p_eval.data.vertices[0].co if p_eval else None)

# Check proxy mesh data vs evaluated data
print("  proxy data vert 0 (rest):", proxy.matrix_world @ proxy.data.vertices[0].co)

# Check proxy modifiers
print("\nProxy modifiers:")
for m in proxy.modifiers:
    print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}")
