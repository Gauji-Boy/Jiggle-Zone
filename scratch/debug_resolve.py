import bpy
from giggle_addon import resolve_garment_target_zone, get_giggle_modifiers, get_mod_socket_attribute_name

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

mods = get_giggle_modifiers(body)
print(f"Mods on body: {[m.name for m in mods]}")

for m in mods:
    vg_name = get_mod_socket_attribute_name(m, 'Socket_2')
    print(f"Mod: {m.name}, vg_name: {vg_name}")

# Test resolve_garment_target_zone
res = resolve_garment_target_zone(top, body)
print(f"resolve_garment_target_zone result: {res}")
