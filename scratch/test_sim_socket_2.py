import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
from giggle_addon import set_mod_socket

body = bpy.data.objects.get('kasumi_body')

bpy.context.scene.frame_set(15)
dg = bpy.context.evaluated_depsgraph_get()
print("1. Frame 15 before:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

# Add Wiggy with Simulate = False:
mod = body.modifiers.new(name="Test_Sim_False", type='NODES')
mod.node_group = bpy.data.node_groups.get("Wiggy 0.1")
set_mod_socket(mod, 'Socket_61', value=False) # Turn off simulation!

with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=1)

dg = bpy.context.evaluated_depsgraph_get()
print("2. Frame 15 with Simulate=False (moved to index 1):", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)

body.modifiers.remove(mod)
