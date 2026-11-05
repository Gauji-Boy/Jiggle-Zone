import bpy

body = bpy.data.objects.get('kasumi_body')

bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Frame 15 before:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

mod = body.modifiers.new(name="Test_Nudge", type='NODES')
mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("2. Immediately after move (1.6308 rest pose):", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

cur_f = bpy.context.scene.frame_current
nudge_f = cur_f + 1 if cur_f < bpy.context.scene.frame_end else cur_f - 1
bpy.context.scene.frame_set(nudge_f)
bpy.context.scene.frame_set(cur_f)

dg = bpy.context.evaluated_depsgraph_get()
print("3. After frame nudge & return to frame 15:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

body.modifiers.remove(mod)
