import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')
from giggle_addon import get_mod_socket

topcen = bpy.data.objects.get('topcen')
body = bpy.data.objects.get('kasumi_body')

mod = topcen.modifiers.get('Giggle_topcen_Follow')
if mod:
    vg = get_mod_socket(mod, 'Socket_2')
    print("Giggle_topcen_Follow Socket_2:", vg)
    
print("topcen vertex groups count:", len(topcen.vertex_groups))
for g in topcen.vertex_groups:
    if 'jiggle' in g.name.lower() or 'breast' in g.name.lower():
        print(f"  topcen: {g.name}")

print("\nkasumi_body vertex groups count:", len(body.vertex_groups))
for g in body.vertex_groups:
    if 'jiggle' in g.name.lower() or 'butt' in g.name.lower():
        print(f"  kasumi_body: {g.name}")
