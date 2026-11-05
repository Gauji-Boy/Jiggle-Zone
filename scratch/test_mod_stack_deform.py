import bpy

body = bpy.data.objects.get('kasumi_body')
for m in list(body.modifiers):
    if 'Test' in m.name:
        body.modifiers.remove(m)

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
print("Starting modifiers on body:", [(m.name, m.type, m.show_viewport) for m in body.modifiers])
print("Initial max_z:", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Now let us disable each modifier one by one and check max_z:
for m in body.modifiers:
    m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    print(f"Disabled {m.name}: max_z = {max(v.co.z for v in body.evaluated_get(dg).data.vertices):.4f}")
    m.show_viewport = True
