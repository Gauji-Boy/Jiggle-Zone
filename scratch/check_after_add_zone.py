import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.new_zone_vg = 'Butt_Zone'
bpy.context.scene.giggle_settings.new_zone_preset = 'STYLE_GLUTES_SOFT'

bpy.ops.giggle.add_zone()

print("Modifiers after add_zone:")
for i, m in enumerate(body.modifiers):
    print(f"  {i}: {m.name} ({m.type}), show_viewport={m.show_viewport}")

dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
print(f"Body Z: [{min(v.co.z for v in b_ev.data.vertices):.3f}, {max(v.co.z for v in b_ev.data.vertices):.3f}]")
