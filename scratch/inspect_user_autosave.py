import bpy
import sys

autosave_path = r"C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_28620_autosave.blend"

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')
topcen = bpy.data.objects.get('topcen')

print("=== INSPECTING USER AUTOSAVE ===")
print("Scene current frame:", bpy.context.scene.frame_current)
print("Scene start/end:", bpy.context.scene.frame_start, bpy.context.scene.frame_end)

if body:
    print(f"\nBody parent: {body.parent}, mode: {body.mode}")
    print("Body modifiers:")
    for m in body.modifiers:
        print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}")
        if m.type == 'ARMATURE':
            print(f"    Armature object={m.object}, vertex_group='{m.vertex_group}'")

if rig:
    print(f"\nRig animation data: {rig.animation_data}")
    if rig.animation_data and rig.animation_data.action:
        print(f"  Action: {rig.animation_data.action.name}, range={rig.animation_data.action.frame_range}")

print("\n=== EVALUATING FRAMES IN AUTOSAVE ===")
for f in [1, 2, 3, 10, 18, 0, 1]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg) if body else None
    t_ev = topcen.evaluated_get(dg) if topcen else None
    
    b_z = max(v.co.z for v in b_ev.data.vertices) if b_ev else 0
    t_z = max(v.co.z for v in t_ev.data.vertices) if t_ev else 0
    print(f"Frame {f:2d}: body_max_z={b_z:.4f}, topcen_max_z={t_z:.4f}")
