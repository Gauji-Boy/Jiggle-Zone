import bpy

kasumi_rig = bpy.data.objects['Kasumi_rig']
act = kasumi_rig.animation_data.action

print('Action name:', act.name)
bone_names_keyed = set()

if hasattr(act, 'fcurves'):
    for fc in act.fcurves:
        dp = fc.data_path
        if 'pose.bones[' in dp:
            bname = dp.split('["')[1].split('"]')[0]
            bone_names_keyed.add(bname)

print('Keyed bones count:', len(bone_names_keyed))
print('Sample keyed bones:', sorted(list(bone_names_keyed))[:30])

# Check FK vs IK properties on Auto Rig Pro
for b in kasumi_rig.pose.bones:
    for k in b.keys():
        if any(w in k.lower() for w in ['ik', 'fk']):
            print(f'Bone {b.name} prop {k} = {b[k]}')
