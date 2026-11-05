import bpy

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')

bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Frame 15 before:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

mod = body.modifiers.new(name="Test_Refresh", type='NODES')
mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("2. Immediately after move:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

# Test 1: body.update_tag(refresh={'OBJECT', 'DATA'})
body.update_tag(refresh={'OBJECT', 'DATA'})
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
print("3. After body.update_tag(refresh={'OBJECT', 'DATA'}):", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

# Test 2: rig update tag as well?
rig.update_tag(refresh={'OBJECT', 'DATA'})
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
print("4. After rig.update_tag too:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

# Test 3: What if we tag the armature modifier itself?
# Or what if we set scene.frame_set?
cur_frame = bpy.context.scene.frame_current
bpy.context.scene.frame_set(cur_frame)
dg = bpy.context.evaluated_depsgraph_get()
print("5. After frame_set(cur_frame):", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

# Test 4: What if we toggle show_viewport on the armature modifier or something?
arm_mod = [m for m in body.modifiers if m.type == 'ARMATURE'][0]
arm_mod.show_viewport = False
arm_mod.show_viewport = True
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
print("6. After arm_mod show_viewport toggle:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

body.modifiers.remove(mod)
