import bpy

for name in ['kasumi_body', 'hair', 'glasses', 'gloves', 'topcen', 'heels', 'leggins', 'Kasumi_rig', 'Kasumi_grp', 'Armature']:
    obj = bpy.data.objects.get(name)
    if obj:
        print(f"Object '{name}':")
        print(f"  parent={obj.parent.name if obj.parent else None}, parent_type={obj.parent_type}, parent_bone={obj.parent_bone}")
        print(f"  matrix_world translation={obj.matrix_world.translation}")
        print(f"  location={obj.location}")
