import bpy
import traceback

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

try:
    print("Testing Candidate A (update_tag):", flush=True)
    body.update_tag(eval_flags={'GEOMETRY'})
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    print("  Candidate A result:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)
except Exception:
    traceback.print_exc()

try:
    print("Testing Candidate B (frame nudge):", flush=True)
    f = bpy.context.scene.frame_current
    bpy.context.scene.frame_set(f + 1)
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    print("  Candidate B result:", max(v.co.z for v in body.evaluated_get(dg).data.vertices), flush=True)
except Exception:
    traceback.print_exc()

body.modifiers.remove(mod)
print("Finished test cleanly!", flush=True)
