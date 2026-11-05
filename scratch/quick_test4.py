
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

    old_softness = settings.zone_softness
    settings.zone_softness = old_softness + 0.05

    print('CAGE MODIFIERS:', [m.name for m in chest_cage.modifiers])
    for m in chest_cage.modifiers:
        print('  mod:', m.name, 'type:', m.type, 'ng:', getattr(m, 'node_group', None))
except Exception:
    traceback.print_exc()
