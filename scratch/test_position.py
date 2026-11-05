import bpy
import sys
sys.path.append(r'd:\Blender\Giggle')

from giggle_addon import position_giggle_modifier

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')

print("=== CHECKING POSITION_GIGGLE_MODIFIER ===")
print("Before:")
for m in body.modifiers:
    print(f"  {m.name} ({m.type})")

mod = body.modifiers.get('Giggle_Jiggle_Zone')
if mod:
    position_giggle_modifier(body, mod)
    print("After position_giggle_modifier:")
    for m in body.modifiers:
        print(f"  {m.name} ({m.type})")

print("Topcen modifiers:")
for m in topcen.modifiers:
    print(f"  {m.name} ({m.type})")
    if m.type == 'SURFACE_DEFORM':
        print(f"    target={m.target.name if m.target else None}, is_bound={m.is_bound}")
