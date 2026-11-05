import bpy

topcen = bpy.data.objects.get('topcen')
print("topcen parent:", topcen.parent)
print("topcen location:", topcen.location)
print("topcen modifiers:")
for m in topcen.modifiers:
    print(f"  {m.name} ({m.type}), show_viewport={m.show_viewport}")
    if m.type == 'SURFACE_DEFORM':
        print(f"    target={m.target}, is_bound={m.is_bound}")
    if m.type == 'NODES':
        print(f"    node_group={m.node_group.name if m.node_group else None}")
