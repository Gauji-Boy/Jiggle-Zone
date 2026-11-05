
import bpy

# Load autosave
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_32240_autosave.blend')

proxy = bpy.data.objects.get('kasumi_body_Jiggle_Zone_Proxy')
cloth = bpy.data.objects.get('topcen')

if not proxy:
    print('Proxy not found in file directly, running attach first...')
    import sys
    sys.path.insert(0, r'd:\Blender\Giggle')
    import giggle_addon
    giggle_addon.register()
    
    body = bpy.data.objects.get('kasumi_body')
    for o in bpy.data.objects:
        o.select_set(False)
    body.select_set(True)
    cloth.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.giggle.attach_clothing_proxy()
    proxy = bpy.data.objects.get('kasumi_body_Jiggle_Zone_Proxy')

print('Proxy found:', proxy.name)
print('Current display_type:', proxy.display_type)
print('Current hide_viewport:', proxy.hide_viewport)
print('Current hide_get():', proxy.hide_get())

# Test hiding proxy
proxy.hide_viewport = True
proxy.hide_set(True)

print('After hide - hide_viewport:', proxy.hide_viewport, 'hide_get():', proxy.hide_get())

# Test deformation evaluation across frames with hidden proxy
sd = cloth.modifiers.get('Giggle_SurfaceDeform')
print('SurfaceDeform is_bound:', sd.is_bound if sd else None)

for f in [1, 10, 20, 28]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    cloth_eval = cloth.evaluated_get(dg)
    body_eval = bpy.data.objects['kasumi_body'].evaluated_get(dg)
    # Check bra vert vs body vert
    v_body = body_eval.matrix_world @ body_eval.data.vertices[2847].co
    v_cloth = cloth_eval.matrix_world @ cloth_eval.data.vertices[0].co
    dist = (v_body - v_cloth).length * 100.0
    print(f'Frame {f}: dist = {dist:.3f} cm')

print('Test completed successfully!')
