import bpy

# Load autosave
bpy.ops.wm.open_mainfile(filepath=r'C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_32240_autosave.blend')

# Test: Check all objects in scene that have SurfaceDeform modifiers
print('=== OBJECTS WITH SURFACE_DEFORM ===')
for obj in bpy.data.objects:
    for mod in obj.modifiers:
        if mod.type == 'SURFACE_DEFORM':
            print(f'Object {obj.name}: modifier {mod.name}, target={mod.target.name if mod.target else None}, is_bound={mod.is_bound}')

# Test: What happens when mod.target is reassigned to another proxy?
# Does is_bound stay True, or does it require unbind/rebind?
top = bpy.data.objects.get('topcen')
sd = top.modifiers.get('Giggle_SurfaceDeform') if top else None
if sd:
    print('\nInitial is_bound:', sd.is_bound)
    # create dummy mesh
    m = bpy.data.meshes.new('dummy_mesh')
    o = bpy.data.objects.new('dummy_obj', m)
    bpy.context.scene.collection.objects.link(o)
    old_target = sd.target
    sd.target = o
    print('After changing target to dummy_obj, is_bound:', sd.is_bound)
    sd.target = old_target
    print('After restoring target, is_bound:', sd.is_bound)
    bpy.data.objects.remove(o)
