import bpy

def get_driving_armature(cage_or_mesh):
    if not cage_or_mesh:
        return None
    for m in getattr(cage_or_mesh, "modifiers", []):
        if m.type == 'ARMATURE' and m.object:
            return m.object
    if cage_or_mesh.parent and getattr(cage_or_mesh.parent, "type", "") == 'ARMATURE':
        return cage_or_mesh.parent
    src_body_name = cage_or_mesh.get('_giggle_source_body')
    if src_body_name:
        src_body = bpy.data.objects.get(src_body_name)
        if src_body:
            for m in getattr(src_body, "modifiers", []):
                if m.type == 'ARMATURE' and m.object:
                    return m.object
            if src_body.parent and getattr(src_body.parent, "type", "") == 'ARMATURE':
                return src_body.parent
    for o in bpy.data.objects:
        if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action:
            return o
    return None

cage = bpy.data.objects.get("Chest_Cage")
arm = get_driving_armature(cage)
print("Driving armature for Chest_Cage:", arm.name if arm else None)
