import bpy

print("=== ALL MESH OBJECTS WITH WIRE OR DISPLAY_TYPE != 'TEXTURED' ===")
for o in bpy.data.objects:
    if o.type == 'MESH':
        if o.display_type != 'TEXTURED' or o.show_wire:
            print(f"{o.name}: display_type={o.display_type}, show_wire={o.show_wire}, hide_v={o.hide_viewport}, hide_get={o.hide_get()}")

print("\n=== ALL OBJECTS WITH 'Proxy' or 'tmp' OR 'Zone' in name ===")
for o in bpy.data.objects:
    if any(k in o.name.lower() for k in ['proxy', 'tmp', 'zone', 'giggle']):
        print(f"{o.name}: type={o.type}, display_type={o.display_type}, hide_v={o.hide_viewport}, hide_get={o.hide_get()}")
        if o.type == 'MESH':
            print(f"   verts={len(o.data.vertices)}, faces={len(o.data.polygons)}")

print("\n=== TOP / CLOTHING MESHES ===")
for o in bpy.data.objects:
    if any(k in o.name.lower() for k in ['top', 'cloth', 'bra', 'bikini']):
        print(f"{o.name}: type={o.type}, hide_v={o.hide_viewport}, hide_get={o.hide_get()}")
        for m in o.modifiers:
            print(f"  {m.name} ({m.type})")
