import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')
topcen = bpy.data.objects.get('topcen')

# Remove existing giggle zones to simulate user adding a zone fresh
for m in list(body.modifiers):
    if 'Giggle' in m.name or m.type == 'NODES':
        body.modifiers.remove(m)

bpy.context.view_layer.objects.active = body
body.select_set(True)

# Set frame to 18 (jump)
bpy.context.scene.frame_set(18)
dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
t_ev = topcen.evaluated_get(dg)
print(f"At Frame 18 before add_zone: body_max_z={max(v.co.z for v in b_ev.data.vertices):.3f}")

# Now add zone!
print("Calling giggle.add_zone...")
bpy.ops.giggle.add_zone(group_name='Jiggle_Zone')

print(f"Current frame after add_zone: {bpy.context.scene.frame_current}")
dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
t_ev = topcen.evaluated_get(dg)
print(f"At frame {bpy.context.scene.frame_current}: body_max_z={max(v.co.z for v in b_ev.data.vertices):.3f}, topcen_max_z={max(v.co.z for v in t_ev.data.vertices):.3f}")

# Check all modifiers on body and their viewport status
for m in body.modifiers:
    print(f"  Body mod: {m.name} ({m.type}), show_viewport={m.show_viewport}")
