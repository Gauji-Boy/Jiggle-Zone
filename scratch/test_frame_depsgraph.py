import bpy

body = bpy.data.objects.get('kasumi_body')

# Let's go to frame 15 first!
bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Frame 15 before move: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

mod = body.modifiers.new(name="Test_Frame15", type='NODES')
mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("2. Frame 15 immediately after move: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
print("3. Frame 1: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("4. Frame 15 after returning from frame 1: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

body.modifiers.remove(mod)
