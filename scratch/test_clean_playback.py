import bpy

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')

print("=== FRESH PLAYBACK SCAN (NO ADDON OPS) ===")
for f in range(0, 10):
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    t_ev = topcen.evaluated_get(dg) if topcen else None
    
    b_z = max(v.co.z for v in b_ev.data.vertices) if b_ev else 0
    t_z = max(v.co.z for v in t_ev.data.vertices) if t_ev else 0
    print(f"Frame {f:2d}: body_max_z={b_z:.4f}, topcen_max_z={t_z:.4f}")
