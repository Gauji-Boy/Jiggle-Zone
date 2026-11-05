import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')

for m in list(body.modifiers):
    if 'Giggle' in m.name or m.type == 'NODES':
        body.modifiers.remove(m)

bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.new_zone_vg = 'Jiggle_Zone'

print("Before add_zone:")
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
print(f"Frame 1 before add_zone: max_z={max(v.co.z for v in b_ev.data.vertices):.4f}")

res = bpy.ops.giggle.add_zone()
print("Result of add_zone:", res)

bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
print(f"Frame 1 after add_zone: max_z={max(v.co.z for v in b_ev.data.vertices):.4f}")

print("\nModifiers on body:")
for m in body.modifiers:
    print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}")
