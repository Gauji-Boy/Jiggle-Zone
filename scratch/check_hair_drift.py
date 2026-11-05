import bpy

body = bpy.data.objects.get('kasumi_body')
hair = bpy.data.objects.get('hair')
gloves = bpy.data.objects.get('gloves')
topcen = bpy.data.objects.get('topcen')
heels = bpy.data.objects.get('heels')

print("=== CHECKING ALL FRAMES FOR BODY VS HAIR VS GLOVES ===")
for f in range(1, 35):
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    h_ev = hair.evaluated_get(dg)
    g_ev = gloves.evaluated_get(dg)
    
    b_max = max(v.co.z for v in b_ev.data.vertices) if b_ev else 0
    h_max = max(v.co.z for v in h_ev.data.vertices) if h_ev else 0
    g_max = max(v.co.z for v in g_ev.data.vertices) if g_ev else 0
    
    print(f"F{f:02d}: body_top={b_max:.3f}, hair_top={h_max:.3f}, diff={h_max - b_max:.3f}, gloves_top={g_max:.3f}")
