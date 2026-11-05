import bpy

print("=== CHECKING MATERIALS OF TOP OBJECTS ===")
for name in ["top", "topcen", "horni.top.001", "horni.top.002"]:
    o = bpy.data.objects.get(name)
    if o:
        mats = [ms.material.name if ms.material else "None" for ms in o.material_slots]
        print(f"{name}: mats={mats}, num_verts={len(o.data.vertices)}")
