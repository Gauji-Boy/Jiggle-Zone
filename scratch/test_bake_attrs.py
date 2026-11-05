import bpy

cage = bpy.data.objects.get("Chest_Cage")
if cage:
    for m in cage.modifiers:
        if m.type == 'NODES' and m.node_group:
            print("Modifier:", m.name, "bakes:", len(m.bakes))
            for i, b in enumerate(m.bakes):
                print(f"Bake #{i}:", type(b))
                for attr in dir(b):
                    if not attr.startswith('__'):
                        try:
                            val = getattr(b, attr)
                            print(f"  {attr} = {val}")
                        except Exception as e:
                            print(f"  {attr} = <ERR: {e}>")
