
import bpy, sys, traceback

try:
    sys.path.insert(0, r'd:\Blender\Giggle')
    import giggle_addon
    giggle_addon.register()

    bpy.ops.wm.open_mainfile(filepath=r'd:\Blender\Giggle\poc_cage_xpbd_kasumi.blend')
    body = bpy.data.objects['kasumi_body']
    settings = bpy.context.scene.giggle_settings

    settings.active_zone_index = 0
    bpy.context.view_layer.objects.active = body
    bpy.ops.giggle.generate_cage(target_verts=450, dilation_rings=2)
    chest_cage = giggle_addon.get_zone_cage_object(body, 'Jiggle_Zone')

    print('READING ZONE SOFTNESS...')
    old_softness = settings.zone_softness
    print('OLD SOFTNESS:', old_softness)
    settings.zone_softness = old_softness + 0.05
    print('NEW SOFTNESS SET!')

    c_mod = next(m for m in chest_cage.modifiers if m.node_group and m.node_group.name == 'Wiggy 0.1')
    print('Body socket_33:', giggle_addon.get_mod_socket(giggle_addon.get_giggle_modifiers(body)[0], 'Socket_33'))
    print('Cage socket_33:', giggle_addon.get_mod_socket(c_mod, 'Socket_33'))
except Exception as e:
    traceback.print_exc()
