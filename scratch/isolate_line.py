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

# Let's run lines of add_zone one by one:
bpy.context.view_layer.objects.active = body
body.select_set(True)
check_z("1. ACTIVE & SELECT")

# Switch to object mode if needed
if body.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
check_z("2. MODE SET OBJECT")

# frame_set
if bpy.context.scene.frame_current > bpy.context.scene.frame_start:
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
check_z("3. FRAME_SET")

# Subsurf mute
subsurf_state = [(m, m.show_viewport, m.levels) for m in body.modifiers if m.type == 'SUBSURF']
for s, was_visible, old_levels in subsurf_state:
    if was_visible: s.show_viewport = False
check_z("4. SUBSURF MUTE")

# add_rest_position_attribute
body.add_rest_position_attribute = True
check_z("5. ADD_REST_POSITION_ATTRIBUTE")

# Add modifier
ng = bpy.data.node_groups.get('Wiggy 0.1')
mod = body.modifiers.new(name="Test_Zone_Debug", type='NODES')
mod.node_group = ng
mod.show_viewport = False
check_z("6. MODIFIERS NEW & MUTE")

# Set socket 2
giggle_addon.set_mod_socket(mod, 'Socket_2', attribute='Jiggle_Zone')
check_z("7. SET SOCKET 2")

# Position modifier
giggle_addon.position_giggle_modifier(body, mod)
check_z("8. POSITION GIGGLE MODIFIER")

# Restore viewport
mod.show_viewport = True
check_z("9. MOD SHOW VIEWPORT TRUE")

# Restore subsurf
for s, was_visible, old_levels in subsurf_state:
    s.show_viewport = was_visible
check_z("10. SUBSURF RESTORE")
