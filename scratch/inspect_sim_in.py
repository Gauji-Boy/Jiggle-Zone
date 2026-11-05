import bpy

ng = bpy.data.node_groups.get("Wiggy 0.1")
sim_in = [n for n in ng.nodes if n.type == 'SIMULATION_INPUT'][0]
print("sim_in type:", type(sim_in))
print("sim_in dir:", [k for k in dir(sim_in) if not k.startswith('_')])
for k in dir(sim_in):
    if not k.startswith('_'):
        try:
            print(f"  {k} = {getattr(sim_in, k)}")
        except Exception:
            pass

# Also check what feeds into sim_in:
print("\nLinks leading to sim_in:")
for inp in sim_in.inputs:
    for l in inp.links:
        print(f"  {inp.name} <-- {l.from_node.name} ({l.from_node.type})")
