import bpy

body = bpy.data.objects.get('kasumi_body')
arm = body.modifiers.get('rig')
print("Armature modifier:", arm.name, "object:", arm.object.name)

# What if we move a modifier to index 2 instead of index 1?
mod = body.modifiers.new(name="Test_Idx2", type='BEVEL')
with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=2)

dg = bpy.context.evaluated_depsgraph_get()
print("After move to index 2: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))
body.modifiers.remove(mod)

# What if we move a modifier to index 3?
mod = body.modifiers.new(name="Test_Idx3", type='BEVEL')
with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=3)

dg = bpy.context.evaluated_depsgraph_get()
print("After move to index 3: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))
body.modifiers.remove(mod)
