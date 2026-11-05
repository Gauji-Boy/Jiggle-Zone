import bpy
import mathutils

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

# Let's test with Wiggy enabled vs disabled
wiggy_mod = body.modifiers.get("Giggle_Jiggle_Zone")

print("Checking kasumi_body deformation with Wiggy ON vs Wiggy OFF at Frame 1, 2, 3:")
for f in [1, 2, 3]:
    bpy.context.scene.frame_set(f)
    
    # Wiggy ON
    wiggy_mod.show_viewport = True
    dg = bpy.context.evaluated_depsgraph_get()
    b_on = body.evaluated_get(dg)
    v_on = [b_on.matrix_world @ v.co for v in b_on.data.vertices[:100]]
    
    # Wiggy OFF
    wiggy_mod.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    b_off = body.evaluated_get(dg)
    v_off = [b_off.matrix_world @ v.co for v in b_off.data.vertices[:100]]
    
    diffs = [(v1 - v2).length for v1, v2 in zip(v_on, v_off)]
    max_diff = max(diffs)
    avg_diff = sum(diffs) / len(diffs)
    print(f"Frame {f}: Wiggy offset on body verts: max={max_diff*100:.3f} cm, avg={avg_diff*100:.3f} cm")
