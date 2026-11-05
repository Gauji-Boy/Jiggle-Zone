import bpy

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')

print("=== CHECKING ALL FRAMES 1 TO 40 ===")
for f in range(1, 41):
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    t_ev = topcen.evaluated_get(dg)
    
    b_z = max(v.co.z for v in b_ev.data.vertices) if b_ev else 0
    t_z = max(v.co.z for v in t_ev.data.vertices) if t_ev else 0
    
    # Check bone c_head.x or c_pos
    head_z = 0
    for pb_name in ['c_head.x', 'c_pos', 'head.x', 'c_traj']:
        pb = rig.pose.bones.get(pb_name)
        if pb:
            head_z = (rig.matrix_world @ pb.matrix).translation.z
            break
            
    print(f"F{f:02d}: head_bone_z={head_z:.2f}, body_max_z={b_z:.2f}, topcen_max_z={t_z:.2f}")
