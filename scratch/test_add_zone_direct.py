import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
for m in list(body.modifiers):
    if 'Giggle' in m.name or m.type == 'NODES':
        body.modifiers.remove(m)

bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.new_zone_vg = 'Jiggle_Zone'

try:
    res = bpy.ops.giggle.add_zone()
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
