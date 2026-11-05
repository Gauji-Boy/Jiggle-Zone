
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

    # Bake
    bpy.ops.giggle.bake_all_cages()
    status_before, _, _ = giggle_addon.get_cage_bake_status(chest_cage)
    print('STATUS BEFORE MOD:', status_before)

    # Change softness
    old_softness = settings.zone_softness
    settings.zone_softness = old_softness + 0.05

    status_after, _, _ = giggle_addon.get_cage_bake_status(chest_cage)
    print('STATUS AFTER MOD:', status_after)

    c_mod = next(m for m in chest_cage.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1')
    body_val = giggle_addon.get_mod_socket(giggle_addon.get_giggle_modifiers(body)[0], 'Socket_33')
    cage_val = giggle_addon.get_mod_socket(c_mod, 'Socket_33')
    print('BODY SOCKET_33:', body_val)
    print('CAGE SOCKET_33:', cage_val)
except Exception:
    traceback.print_exc()
