import bpy

body = bpy.data.objects.get('kasumi_body')
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Initial Frame 1 max_z:", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

# Just call modifier_move_to_index on an existing modifier or add a simple modifier
mod = body.modifiers.new(name="Dummy", type='BEVEL')
print("2. Added Bevel max_z:", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("3. Moved Bevel to index 1 max_z:", max(v.co.z for v in body.evaluated_get(dg).data.vertices))

body.modifiers.remove(mod)
dg = bpy.context.evaluated_depsgraph_get()
print("4. Removed Bevel max_z:", max(v.co.z for v in body.evaluated_get(dg).data.vertices))
