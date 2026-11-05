import bpy

ng = bpy.data.node_groups.get("Wiggy 0.1")
print("=== WIGGY 0.1 NODES ===")
for node in ng.nodes:
    print(f"Node: '{node.name}', type: {node.type}, label: '{node.label}'")
    if node.type in ('SIMULATION_INPUT', 'SIMULATION_OUTPUT'):
        print(f"  Simulation node: {node.name}")
        for item in node.inputs:
            print(f"    input: {item.name}")
        for item in node.outputs:
            print(f"    output: {item.name}")

# Let us check any Frame or Simulation State nodes:
for node in ng.nodes:
    if "FRAME" in node.type or "TIME" in node.type or "SIM" in node.type or "REST" in node.name.upper():
        print(f"\nSpecial node: {node.name} ({node.type})")
        for in_sock in node.inputs:
            links = in_sock.links
            if links:
                for l in links:
                    print(f"  Input '{in_sock.name}' <-- '{l.from_node.name}'.'{l.from_socket.name}'")
            else:
                val = getattr(in_sock, 'default_value', None)
                print(f"  Input '{in_sock.name}' (default): {val}")
