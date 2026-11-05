import bpy

rig = bpy.data.objects.get('Kasumi_rig')
body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')

for f in [0, 1, 2, 3]:
    bpy.context.scene.frame_set(f)
    print(f"\n================ FRAME {f} ================")
    
    # Check Kasumi_rig pose bones: spine, arms, legs
    for b in ['c_spine_01.x', 'c_arm_ik.l', 'c_arm_fk.l', 'c_hand_ik.l', 'c_hand_fk.l', 'c_thigh_ik.l', 'c_thigh_fk.l', 'c_foot_ik.l']:
        pb = rig.pose.bones.get(b)
        if pb:
            mw = rig.matrix_world @ pb.matrix
            print(f"  Rig bone '{b}': world pos={mw.translation}")
            
    # Check body vertices
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    t_ev = topcen.evaluated_get(dg)
    
    b_zs = [v.co.z for v in b_ev.data.vertices]
    t_zs = [v.co.z for v in t_ev.data.vertices]
    print(f"  Evaluated body Z: [{min(b_zs):.3f}, {max(b_zs):.3f}]")
    print(f"  Evaluated topcen Z: [{min(t_zs):.3f}, {max(t_zs):.3f}]")
