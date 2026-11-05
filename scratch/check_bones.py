import bpy

rig = bpy.data.objects.get('Kasumi_rig')
act = rig.animation_data.action if rig and rig.animation_data else None

print("=== RIG ACTION CHECK ===")
if act:
    print(f"Action: {act.name}")
    bone_names = set()
    for fc in act.fcurves:
        dp = fc.data_path
        if 'pose.bones[' in dp:
            bname = dp.split('["')[1].split('"]')[0]
            bone_names.add(bname)
    print("Animated bones count:", len(bone_names))
    print("Animated bones:", sorted(list(bone_names)))
else:
    print("No action on Kasumi_rig")
