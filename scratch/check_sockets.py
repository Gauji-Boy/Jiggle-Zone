import bpy

cage = bpy.data.objects.get("Chest_Cage")
mod = next(m for m in cage.modifiers if m.type == 'NODES' and m.node_group.name == 'Wiggy 0.1')
s_in = getattr(mod.properties, "inputs")
for k in dir(s_in):
    if k.startswith("Socket_"):
        sock = getattr(s_in, k)
        val = getattr(sock, "value", None)
        print(f"  {k}: val={val}")
