import bpy

arm = bpy.data.objects.get('Armature')
if arm and arm.animation_data and arm.animation_data.action:
    act = arm.animation_data.action
    print(f"Armature action: {act.name}")
    print(f"Action frame range: {act.frame_range}")
    for f in range(1, 15):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        a_ev = arm.evaluated_get(dg)
        # check bone positions or mesh children of Armature
        for child in arm.children:
            c_ev = child.evaluated_get(dg)
            zs = [v.co.z for v in c_ev.data.vertices] if len(c_ev.data.vertices) > 0 else [0]
            print(f"  F{f}: child '{child.name}' max_z={max(zs):.2f}")
            break
