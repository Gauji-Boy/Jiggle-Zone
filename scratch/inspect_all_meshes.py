import bpy

print("=== CHECKING ALL MESH OBJECTS DEFORMATION AT FRAME 1 ===")
bpy.context.scene.frame_set(1)

for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    if obj.name.startswith('cs_'):
        continue
    
    arm_mods = [m for m in obj.modifiers if m.type == 'ARMATURE']
    node_mods = [m for m in obj.modifiers if m.type == 'NODES']
    surf_mods = [m for m in obj.modifiers if m.type == 'SURFACE_DEFORM']
    
    print(f"\nObject '{obj.name}': parent={obj.parent.name if obj.parent else None}")
    print(f"  Armature modifiers: {[(m.name, m.object.name if m.object else None, m.show_viewport) for m in arm_mods]}")
    print(f"  Nodes modifiers: {[(m.name, m.node_group.name if m.node_group else None, m.show_viewport) for m in node_mods]}")
    print(f"  SurfaceDeform: {[(m.name, m.target.name if m.target else None, m.is_bound, m.show_viewport) for m in surf_mods]}")
    
    # Calculate center of mass / bounding box at frame 1
    dg = bpy.context.evaluated_depsgraph_get()
    o_ev = obj.evaluated_get(dg)
    if len(o_ev.data.vertices) > 0:
        zs = [v.co.z for v in o_ev.data.vertices]
        print(f"  Evaluated Z range: [{min(zs):.2f}, {max(zs):.2f}], avg={sum(zs)/len(zs):.2f}")
