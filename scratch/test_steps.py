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

bpy.context.scene.frame_set(18)

try:
    print("Step 1: check frame_set...")
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    print("Step 2: add_rest_position_attribute...")
    body.add_rest_position_attribute = True
    print("Step 3: add modifier...")
    mod = body.modifiers.new(name="Test_Zone", type='NODES')
    ng = bpy.data.node_groups.get('Wiggy 0.1')
    mod.node_group = ng
    mod.show_viewport = False
    print("Step 4: set_mod_socket...")
    giggle_addon.set_mod_socket(mod, 'Socket_2', attribute='Jiggle_Zone')
    print("Step 5: position_giggle_modifier...")
    giggle_addon.position_giggle_modifier(body, mod)
    print("Step 6: mod.show_viewport = True...")
    mod.show_viewport = True
    print("Step 7: done!")
except Exception as e:
    import traceback
    traceback.print_exc()
