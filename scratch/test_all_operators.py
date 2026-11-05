import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
import giggle_addon

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')
hair = bpy.data.objects.get('hair')

def check_positions(tag):
    bpy.context.scene.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg) if body else None
    t_ev = topcen.evaluated_get(dg) if topcen else None
    h_ev = hair.evaluated_get(dg) if hair else None
    
    b_z = max(v.co.z for v in b_ev.data.vertices) if b_ev else 0
    t_z = max(v.co.z for v in t_ev.data.vertices) if t_ev else 0
    h_z = max(v.co.z for v in h_ev.data.vertices) if h_ev else 0
    print(f"[{tag}] Frame 1: body_max_z={b_z:.3f}, topcen_max_z={t_z:.3f}, hair_max_z={h_z:.3f}")

check_positions("BEFORE")

# Test 1: Rebind modifiers
print("\n--- Testing giggle.rebind_clothing_modifiers ---")
bpy.ops.object.select_all(action='DESELECT')
for o in [body, topcen, hair]:
    if o: o.select_set(True)
bpy.context.view_layer.objects.active = topcen
try:
    bpy.ops.giggle.rebind_clothing_modifiers()
except Exception as e:
    print("rebind error:", e)
check_positions("AFTER REBIND")

# Test 2: Copy zone to clothing
print("\n--- Testing giggle.copy_zone_to_clothing ---")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
topcen.select_set(True)
bpy.context.scene.giggle_settings.active_zone_index = 0
try:
    bpy.ops.giggle.copy_zone_to_clothing()
except Exception as e:
    print("copy_zone error:", e)
check_positions("AFTER COPY ZONE")

# Test 3: Add new zone
print("\n--- Testing giggle.add_zone ---")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.new_zone_vg = 'Butt_Zone'
bpy.context.scene.giggle_settings.new_zone_preset = 'STYLE_GLUTES_SOFT'
try:
    bpy.ops.giggle.add_zone()
except Exception as e:
    print("add_zone error:", e)
check_positions("AFTER ADD ZONE")

# Test 4: Apply action safety
print("\n--- Testing giggle.apply_action_safety ---")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.context.scene.giggle_settings.active_zone_index = 0
try:
    bpy.ops.giggle.apply_action_safety()
except Exception as e:
    print("apply_action_safety error:", e)
check_positions("AFTER ACTION SAFETY")
