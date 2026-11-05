import bpy

ng = bpy.data.node_groups.get("Wiggy 0.1")
print("=== WIGGY 0.1 INTERFACE ITEMS ===")
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET':
        print(f"Socket: {item.identifier} -> name='{item.name}', in_out={item.in_out}, default={getattr(item, 'default_value', None)}")
