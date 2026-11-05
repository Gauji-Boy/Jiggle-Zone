import bpy

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')
topcen = bpy.data.objects.get('topcen')
hair = bpy.data.objects.get('hair')

print("=== CHECKING OBJECT PARENTS AND MODIFIERS ===")
for obj in [body, topcen, hair]:
    if obj:
        print(f"Object {obj.name}:")
        print(f"  parent: {obj.parent.name if obj.parent else None}")
        print(f"  modifiers: {[(m.name, m.type, m.show_viewport) for m in obj.modifiers]}")

bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

# Let's inspect vertex 0 or bounding box of body with modifiers on vs off
print("=== FRAME 1 TEST ===")
print("With all modifiers ON:")
depsgraph = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(depsgraph)
v_z = [v.co.z for v in b_eval.data.vertices]
print(f"  body Z: min={min(v_z):.3f}, max={max(v_z):.3f}")

# Now turn off Giggle modifiers
for m in body.modifiers:
    if m.type == 'NODES':
        m.show_viewport = False
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(depsgraph)
v_z = [v.co.z for v in b_eval.data.vertices]
print("With Giggle modifiers OFF:")
print(f"  body Z: min={min(v_z):.3f}, max={max(v_z):.3f}")

# Now turn off Armature modifier
for m in body.modifiers:
    if m.type == 'ARMATURE':
        m.show_viewport = False
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(depsgraph)
v_z = [v.co.z for v in b_eval.data.vertices]
print("With Armature modifier OFF:")
print(f"  body Z: min={min(v_z):.3f}, max={max(v_z):.3f}")
