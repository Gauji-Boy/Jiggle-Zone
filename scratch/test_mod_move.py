import bpy

body = bpy.data.objects.get('kasumi_body')
print("Original modifiers:", [(m.name, m.type) for m in body.modifiers])

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
print("Before any changes: max_z =", max(v.co.z for v in b_ev.data.vertices))

ng = bpy.data.node_groups.get("Wiggy 0.1")
mod = body.modifiers.new(name="Test_Move", type='NODES')
mod.node_group = ng
print("After new modifier:", [(m.name, m.type) for m in body.modifiers])
dg = bpy.context.evaluated_depsgraph_get()
print("After new modifier: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)
print("After move_to_index(1):", [(m.name, m.type) for m in body.modifiers])

dg = bpy.context.evaluated_depsgraph_get()
print("After move_to_index(1): max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Now let us test if changing frame restores it:
for f in [2, 3, 1, 0, 1]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    print(f"Frame {f}: max_z = {max(v.co.z for v in body.evaluated_get(dg).data.vertices)}")
