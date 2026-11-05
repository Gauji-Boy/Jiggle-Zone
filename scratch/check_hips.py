import bpy

kasumi_rig = bpy.data.objects['Kasumi_rig']
mixamo = bpy.data.objects['Armature']
scene = bpy.context.scene

print('=== ROOT / HIPS BONE TRANSFORMS ===')
for f in [1, 2, 3, 4, 5]:
    scene.frame_set(f)
    print(f'Frame {f}:')
    # Kasumi root / hips
    for bname in ['c_root_master.x', 'c_pos', 'root.x', 'c_root.x', 'c_spine_01.x']:
        pb = kasumi_rig.pose.bones.get(bname)
        if pb:
            wpos = kasumi_rig.matrix_world @ pb.head
            print(f'   Kasumi {bname} world: ({wpos.x:.3f}, {wpos.y:.3f}, {wpos.z:.3f})')
            break
            
    # Mixamo hips
    for bname in ['mixamorig:Hips', 'Hips']:
        pb = mixamo.pose.bones.get(bname)
        if pb:
            wpos = mixamo.matrix_world @ pb.head
            print(f'   Mixamo {bname} world: ({wpos.x:.3f}, {wpos.y:.3f}, {wpos.z:.3f})')
            break
