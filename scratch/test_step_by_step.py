import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')

body = bpy.data.objects.get("kasumi_body")
print("Has add_rest_position_attribute?", hasattr(body, "add_rest_position_attribute"), hasattr(body.data, "add_rest_position_attribute"))

def check(label):
    bpy.context.scene.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    b = body.evaluated_get(dg)
    print(f"{label}: max_z = {max(v.co.z for v in b.data.vertices):.4f}")

check("1. Start")

# Let us check obj.mode switch
print("Current mode:", body.mode)
if body.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
check("2. After mode_set OBJECT")

# Subsurf state mute
subsurf_state = [(m, m.show_viewport, m.levels) for m in body.modifiers if m.type == 'SUBSURF']
for s, was_visible, old_levels in subsurf_state:
    if was_visible:
        s.show_viewport = False
check("3. After muting subsurf")

# New NODES mod
ng = bpy.data.node_groups.get("Wiggy 0.1")
mod = body.modifiers.new(name="Test_Zone", type='NODES')
mod.node_group = ng
mod.show_viewport = False
check("4. After new NODES mod (viewport false)")

from giggle_addon import set_mod_socket, position_giggle_modifier

set_mod_socket(mod, 'Socket_2', attribute='Butt_Zone')
check("5. After set Socket_2")

position_giggle_modifier(body, mod)
check("6. After position_giggle_modifier")

mod.show_viewport = True
check("7. After show_viewport True")

for s, was_visible, old_levels in subsurf_state:
    s.show_viewport = was_visible
check("8. After restore subsurf")
