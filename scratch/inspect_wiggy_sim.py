import bpy

ng = bpy.data.node_groups.get("Wiggy 0.1")
out_node = [n for n in ng.nodes if n.type == 'GROUP_OUTPUT'][0]
print("Group Output connected to:")
for inp in out_node.inputs:
    for l in inp.links:
        print(f"  {inp.name} <-- {l.from_node.name} ({l.from_node.type}) . {l.from_socket.name}")

sim_in = [n for n in ng.nodes if n.type == 'SIMULATION_INPUT'][0]
sim_out = [n for n in ng.nodes if n.type == 'SIMULATION_OUTPUT'][0]

print("\nSimulation Input:")
for inp in sim_in.inputs:
    for l in inp.links:
        print(f"  {inp.name} <-- {l.from_node.name} ({l.from_node.type}) . {l.from_socket.name}")

print("\nSimulation Output:")
for inp in sim_out.inputs:
    for l in inp.links:
        print(f"  {inp.name} <-- {l.from_node.name} ({l.from_node.type}) . {l.from_socket.name}")
