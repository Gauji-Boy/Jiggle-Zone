import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
hair = bpy.data.objects.get('hair')

def check_z(step_name):
    bpy.context.scene.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    t_ev = topcen.evaluated_get(dg)
    b_z = max(v.co.z for v in b_ev.data.vertices)
    t_z = max(v.co.z for v in t_ev.data.vertices)
    print(f"[{step_name}] body_z={b_z:.3f}, topcen_z={t_z:.3f}")

check_z("0. START")

# Run copy_zone_to_clothing
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
topcen.select_set(True)
bpy.context.scene.giggle_settings.active_zone_index = 0
bpy.ops.giggle.copy_zone_to_clothing()
check_z("1. AFTER COPY ZONE")

# Now rebind
bpy.ops.giggle.rebind_clothing_modifiers()
check_z("2. AFTER REBIND")

# Now add_zone
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.new_zone_vg = 'Butt_Zone'
bpy.context.scene.giggle_settings.new_zone_preset = 'STYLE_GLUTES_SOFT'
bpy.ops.giggle.add_zone()
check_z("3. AFTER ADD ZONE")
