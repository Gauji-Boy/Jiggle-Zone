import bpy

# Load fresh without our attach script changes
body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)
t_eval = top.evaluated_get(dg)

print(f"Body has {len(b_eval.data.vertices)} verts, top has {len(t_eval.data.vertices)} verts")

# Check modifiers on top right now in the blend file
print("Top modifiers in blend file:")
for m in top.modifiers:
    print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}")

# Let's check kasumi_body modifiers in blend file
print("kasumi_body modifiers in blend file:")
for m in body.modifiers:
    print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}")
    if m.type == 'NODES' and m.node_group:
        print(f"    node_group: {m.node_group.name}")
        for k in m.node_group.inputs.keys():
            print(f"      input: {k}")

# Check if Wiggy is currently enabled on body
wiggy_mod = next((m for m in body.modifiers if m.type == 'NODES' and m.node_group and 'Wiggy' in m.node_group.name), None)
if wiggy_mod:
    print(f"Wiggy modifier is on kasumi_body: {wiggy_mod.name}")
