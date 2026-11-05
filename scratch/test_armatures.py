import bpy

body = bpy.data.objects.get('kasumi_body')
for m in body.modifiers:
    if m.type == 'ARMATURE':
        print(f"Body Armature modifier: {m.name}, target object: {m.object.name if m.object else None}")

for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print(f"Armature object: {o.name}, parent={o.parent}, pose_position={o.data.pose_position}")
        if o.animation_data and o.animation_data.action:
            print(f"  Action: {o.animation_data.action.name}")
        else:
            print("  No action")
