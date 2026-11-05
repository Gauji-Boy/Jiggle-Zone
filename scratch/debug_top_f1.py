import bpy

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

# Ensure top is bound to proxy
print("Binding top to proxy if needed...")
sd = top.modifiers.get("Giggle_SurfaceDeform")
if not sd or not sd.is_bound:
    bpy.ops.object.select_all(action='DESELECT')
    top.select_set(True)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.giggle.attach_clothing_proxy()

sd = top.modifiers.get("Giggle_SurfaceDeform")
print(f"top Giggle_SurfaceDeform target: {sd.target.name}, is_bound={sd.is_bound}")

print("\nTracking top vertex 0 at Frame 1 vs Frame 2:")
for f in [1, 2]:
    print(f"\n=== FRAME {f} ===")
    bpy.context.scene.frame_set(f)
    
    # Check top without SurfaceDeform
    sd.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    t_eval = top.evaluated_get(dg)
    print(f"  Top without SurfaceDeform: {t_eval.matrix_world @ t_eval.data.vertices[0].co}")
    
    # Check top with SurfaceDeform
    sd.show_viewport = True
    dg = bpy.context.evaluated_depsgraph_get()
    t_eval = top.evaluated_get(dg)
    print(f"  Top WITH SurfaceDeform:    {t_eval.matrix_world @ t_eval.data.vertices[0].co}")
    
    # Check body vert 791
    b_eval = body.evaluated_get(dg)
    print(f"  Body vert 791:             {b_eval.matrix_world @ b_eval.data.vertices[791].co}")
