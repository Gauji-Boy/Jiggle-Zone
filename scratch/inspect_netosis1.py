import bpy

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')

print("=== NETOSISKASUMI.BLEND INSPECTION ===")
print("Body modifiers:")
for m in body.modifiers:
    print(f"  {m.name} ({m.type}): show_viewport={m.show_viewport}, show_render={m.show_render}")
    if m.type == 'ARMATURE':
        print(f"    object={m.object}, use_vertex_groups={m.use_vertex_groups}")
    if m.type == 'NODES':
        print(f"    node_group={m.node_group.name if m.node_group else None}")

print("Topcen modifiers:")
for m in topcen.modifiers:
    print(f"  {m.name} ({m.type}): show_viewport={m.show_viewport}")
    if m.type == 'ARMATURE':
        print(f"    object={m.object}")

print("Rig pose_position:", rig.data.pose_position if rig else None)
print("Rig action:", rig.animation_data.action.name if rig and rig.animation_data and rig.animation_data.action else None)

# Check frame 1 vs frame 2 vs frame 0
for f in [0, 1, 2, 3]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    t_ev = topcen.evaluated_get(dg)
    b_z = max(v.co.z for v in b_ev.data.vertices)
    t_z = max(v.co.z for v in t_ev.data.vertices)
    print(f"Frame {f}: body_max_z={b_z:.3f}, topcen_max_z={t_z:.3f}")
