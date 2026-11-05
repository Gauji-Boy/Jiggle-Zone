import bpy
import sys

print("=== SCENE INFO ===", flush=True)
print("Frame current:", bpy.context.scene.frame_current, flush=True)
print("Frame start/end:", bpy.context.scene.frame_start, bpy.context.scene.frame_end, flush=True)

body = bpy.data.objects.get("kasumi_body")
rig = bpy.data.objects.get("Kasumi_rig")
topcen = bpy.data.objects.get("topcen")

if body:
    print("=== KASUMI BODY ===", flush=True)
    print("Parent:", body.parent, body.parent_type, flush=True)
    print("Location:", body.location, flush=True)
    print("Modifiers:", flush=True)
    for m in body.modifiers:
        print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}", flush=True)

if rig:
    print("=== RIG ===", flush=True)
    if rig.animation_data and rig.animation_data.action:
        act = rig.animation_data.action
        print(f"  Action name: {act.name}, frame_range: {act.frame_range}", flush=True)

print("=== CHECKING FRAMES ===", flush=True)
for f in [0, 1, 2, 3, 10, 20]:
    bpy.context.scene.frame_set(f)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(depsgraph) if body else None
    t_eval = topcen.evaluated_get(depsgraph) if topcen else None
    
    if b_eval and len(b_eval.data.vertices) > 0:
        b_zs = [v.co.z for v in b_eval.data.vertices]
        b_min_z, b_max_z = min(b_zs), max(b_zs)
    else:
        b_min_z, b_max_z = 0, 0
        
    if t_eval and len(t_eval.data.vertices) > 0:
        t_zs = [v.co.z for v in t_eval.data.vertices]
        t_min_z, t_max_z = min(t_zs), max(t_zs)
    else:
        t_min_z, t_max_z = 0, 0
        
    print(f"Frame {f:2d}: body Z=[{b_min_z:.2f}, {b_max_z:.2f}], topcen Z=[{t_min_z:.2f}, {t_max_z:.2f}]", flush=True)

print("DONE!", flush=True)
