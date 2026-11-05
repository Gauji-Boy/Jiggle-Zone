import bpy

body = bpy.data.objects.get("kasumi_body")
for m in body.modifiers:
    if m.type == 'NODES' and m.node_group:
        ng = m.node_group
        print(f"Modifier: {m.name}, NodeGroup: {ng.name}")
        # Find Simulation Zone in ng
        sim_nodes = [n for n in ng.nodes if n.type in ('SIMULATION_INPUT', 'SIMULATION_OUTPUT')]
        print(f"Simulation nodes: {[n.name for n in sim_nodes]}")
        # Look at inputs to ng
        for inp in ng.inputs:
            val = m.get(inp.identifier) if hasattr(m, 'get') else None
            print(f"  Input: {inp.name} (id: {inp.identifier}) = {val}")
