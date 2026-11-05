import bpy

print("=== ALL MESH OBJECTS ===")
for o in bpy.data.objects:
    if o.type == 'MESH':
        print(f"Mesh: {o.name}, parent={o.parent.name if o.parent else None}, users_collection={[c.name for c in o.users_collection]}")
        for m in o.modifiers:
            print(f"   mod: {m.name} ({m.type}), active={m.show_viewport}")
            if m.type == 'NODES' and m.node_group:
                print(f"      node_group: {m.node_group.name}, bakes={len(m.bakes)}")
                for b in m.bakes:
                    print(f"        bake: {b.name}, blocks={len(b.data_blocks)}")
