
import bpy, sys
sys.path.insert(0, r'd:\Blender\Giggle')
import giggle_addon

bpy.ops.wm.open_mainfile(filepath=r'C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_32240_autosave.blend')
giggle_addon.register()

body = bpy.data.objects['kasumi_body']
top = bpy.data.objects['topcen']

for o in bpy.data.objects:
    o.select_set(False)
body.select_set(True)
top.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.giggle.attach_clothing_proxy()

proxy = bpy.data.objects['kasumi_body_Jiggle_Zone_Proxy']
v_breast_idx = 791

def check_dist(label):
    print(f'=== {label} ===')
    for f in [1, 10, 20, 28, 40]:
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        b_eval = body.evaluated_get(dg)
        t_eval = top.evaluated_get(dg)
        b_pos = b_eval.matrix_world @ b_eval.data.vertices[v_breast_idx].co
        closest_d = min((t_eval.matrix_world @ v.co - b_pos).length for v in t_eval.data.vertices)
        print(f'Frame {f:2d}: Distance = {closest_d*100:.3f} cm')

check_dist('PROXY VISIBLE')

proxy.hide_viewport = True
check_dist('PROXY HIDE_VIEWPORT = TRUE')

proxy.hide_viewport = False
proxy.hide_set(True)
check_dist('PROXY HIDE_SET = TRUE')
