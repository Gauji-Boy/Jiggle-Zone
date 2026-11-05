import bpy, sys
sys.path.insert(0, r'd:\Blender\Giggle')
import giggle_addon

bpy.ops.wm.open_mainfile(filepath=r'C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_32240_autosave.blend')
giggle_addon.register()

body = bpy.data.objects['kasumi_body']
top = bpy.data.objects['topcen']
scene = bpy.context.scene

# Select body and topcen and run attach
for o in bpy.data.objects:
    o.select_set(False)
body.select_set(True)
top.select_set(True)
bpy.context.view_layer.objects.active = body

bpy.ops.giggle.attach_clothing_proxy()

print('\n=== MEASURING VERTEX-BY-VERTEX DISTANCES AT FRAME 1, 2, 3, 4 ===')
v_breast_idx = 791

for f in [1, 2, 3, 4, 10, 20, 28, 33]:
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(dg)
    t_eval = top.evaluated_get(dg)
    b_mesh = b_eval.to_mesh()
    t_mesh = t_eval.to_mesh()
    
    b_pos = b_eval.matrix_world @ b_mesh.vertices[v_breast_idx].co
    closest_d = min((t_eval.matrix_world @ v.co - b_pos).length for v in t_mesh.vertices)
    
    # Also find max distance for vertices that should be attached
    # Let's check average distance of all bra vertices to the nearest body vertex
    b_verts = [b_eval.matrix_world @ v.co for v in b_mesh.vertices]
    # sample 10 bra vertices
    t_samples = [t_eval.matrix_world @ t_mesh.vertices[i*10].co for i in range(min(20, len(t_mesh.vertices)//10))]
    
    b_eval.to_mesh_clear()
    t_eval.to_mesh_clear()
    print(f'Frame {f:2d}: Breast-to-bra = {closest_d*100:.3f} cm')
