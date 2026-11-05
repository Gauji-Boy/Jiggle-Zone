
import bpy, sys, time

sys.path.insert(0, r'd:\Blender\Giggle')
import giggle_addon
giggle_addon.register()

bpy.ops.wm.open_mainfile(filepath=r'd:\Blender\Giggle\poc_cage_xpbd_kasumi.blend')
body = bpy.data.objects['kasumi_body']
scene = bpy.context.scene
settings = scene.giggle_settings

# Generate cage
settings.active_zone_index = 0
bpy.context.view_layer.objects.active = body
bpy.ops.giggle.generate_cage(target_verts=450, dilation_rings=2)
chest_cage = giggle_addon.get_zone_cage_object(body, 'Jiggle_Zone')

# Bake
bpy.ops.giggle.bake_all_cages()
status_before, _, _ = giggle_addon.get_cage_bake_status(chest_cage)
print('Status before mod:', status_before)

# Re-activate body explicitly
bpy.context.view_layer.objects.active = body
old_softness = settings.zone_softness
settings.zone_softness = old_softness + 0.05

status_after, _, _ = giggle_addon.get_cage_bake_status(chest_cage)
print('Status after zone_softness change:', status_after)
c_mod = next(m for m in chest_cage.modifiers if m.name == 'Wiggy 0.1')
print('Cage socket_33:', giggle_addon.get_mod_socket(c_mod, 'Socket_33'))
