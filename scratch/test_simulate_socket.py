import bpy

body = bpy.data.objects.get('kasumi_body')

bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Frame 15 with current stack:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

# Let us check the existing Giggle modifiers on body
giggle_mods = [m for m in body.modifiers if 'Giggle' in m.name]
for m in giggle_mods:
    print(f"Mod {m.name}: show_viewport={m.show_viewport}, node_group={m.node_group.name if m.node_group else None}")
    for k in m.keys():
        if 'Socket_61' in k: # Simulate
            print(f"  {k} (Simulate) = {m[k]}")

# Now let us test what happens if we add Wiggy with Simulate = False vs True:
mod = body.modifiers.new(name="Test_Sim_False", type='NODES')
mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")
mod["Socket_61"] = False # Turn off simulation!

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("2. Frame 15 with Simulate=False:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

body.modifiers.remove(mod)
