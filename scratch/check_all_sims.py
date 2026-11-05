import bpy

ng = bpy.data.node_groups.get("Wiggy 0.1")
sim_ins = [n for n in ng.nodes if n.type == 'SIMULATION_INPUT']
print(f"Total Simulation Inputs: {len(sim_ins)}")
for s in sim_ins:
    print(f"  {s.name} ({s.label})")

sim_outs = [n for n in ng.nodes if n.type == 'SIMULATION_OUTPUT']
print(f"Total Simulation Outputs: {len(sim_outs)}")
for s in sim_outs:
    print(f"  {s.name} ({s.label})")
