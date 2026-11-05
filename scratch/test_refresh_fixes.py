import bpy

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')

bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Frame 15 before:", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

mod = body.modifiers.new(name="Test_Refresh", type='NODES')
mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("2. Immediately after move (expect rest pose 1.6308):", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Now test candidate fixes to refresh the armature without moving the timeline:
# Candidate A: obj.update_tag()
body.update_tag(eval_flags={'GEOMETRY', 'TRANSFORM', 'MODIFIERS'})
dg.update()
print("3. After body.update_tag + dg.update():", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Candidate B: rig.update_tag()
rig.update_tag(eval_flags={'TRANSFORM', 'POSE'})
dg.update()
print("4. After rig.update_tag + dg.update():", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Candidate C: frame_set to current frame or view_layer.update()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
print("5. After view_layer.update():", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Candidate D: frame_set(frame_current)
f_cur = bpy.context.scene.frame_current
bpy.context.scene.frame_set(f_cur)
dg = bpy.context.evaluated_depsgraph_get()
print("6. After frame_set(f_cur):", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Candidate E: micro frame nudge (f_cur + 1, then f_cur) or scene update
bpy.context.scene.frame_set(f_cur + 1 if f_cur < bpy.context.scene.frame_end else f_cur - 1)
bpy.context.scene.frame_set(f_cur)
dg = bpy.context.evaluated_depsgraph_get()
print("7. After 1-tick frame toggle (nudge & back):", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

body.modifiers.remove(mod)
