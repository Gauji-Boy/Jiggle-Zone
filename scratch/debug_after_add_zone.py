import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')

# Rebind
bpy.ops.giggle.rebind_clothing_modifiers()

# Add zone
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.new_zone_vg = 'Butt_Zone'
bpy.context.scene.giggle_settings.new_zone_preset = 'STYLE_GLUTES_SOFT'
bpy.ops.giggle.add_zone()

print("=== INSPECTING BODY AFTER ADD ZONE ===")
for i, m in enumerate(body.modifiers):
    print(f"Mod {i}: {m.name} ({m.type}), show_viewport={m.show_viewport}")
    if m.type == 'ARMATURE':
        print(f"  Armature: object={m.object}, show_in_editmode={m.show_in_editmode}")

print("Body mode:", body.mode)
print("Scene frame:", bpy.context.scene.frame_current)

# Now what happens if we toggle each modifier's show_viewport?
dg = bpy.context.evaluated_depsgraph_get()
b_ev = body.evaluated_get(dg)
print(f"Initial body_z: {max(v.co.z for v in b_ev.data.vertices):.3f}")

for m in body.modifiers:
    m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    print(f"Without {m.name}: body_z={max(v.co.z for v in b_ev.data.vertices):.3f}")
    m.show_viewport = True
