
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

# Touch zone
active_mod = giggle_addon.get_giggle_modifiers(body)[0]
giggle_addon.mark_mod_customized(active_mod)
status_after, _, _ = giggle_addon.get_cage_bake_status(chest_cage)
print('Status after mark_mod_customized:', status_after)
