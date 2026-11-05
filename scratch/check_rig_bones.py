import bpy

rig = bpy.data.objects.get('Kasumi_rig')
body = bpy.data.objects.get('kasumi_body')

for f in [1, 2, 0]:
    bpy.context.scene.frame_set(f)
    print(f"\n--- Frame {f} ---")
    bone = rig.pose.bones.get('c_spine_02.x')
    if bone:
        print(f"c_spine_02.x location: {bone.location}, rotation: {bone.rotation_euler or bone.rotation_quaternion}")
    head = rig.pose.bones.get('c_head.x')
    if head:
        print(f"c_head.x head matrix pos: {head.matrix.translation}")
    
    # Check Kasumi_rig evaluated in depsgraph:
    dg = bpy.context.evaluated_depsgraph_get()
    rig_eval = rig.evaluated_get(dg)
    head_eval = rig_eval.pose.bones.get('c_head.x')
    if head_eval:
        print(f"Evaluated c_head.x pos: {head_eval.matrix.translation}")
