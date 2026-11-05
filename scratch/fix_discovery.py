INIT_PATH = r"d:\Blender\Giggle\giggle_addon\__init__.py"
with open(INIT_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

old_disc = "if o.type == 'MESH' and (o.get('_giggle_cage') or (o.users_collection and any(c.name == 'Giggle_Cages' for c in o.users_collection))):"
new_disc = "if o.type == 'MESH' and (o.get('_giggle_cage') or o.name.endswith('_Cage') or (o.users_collection and any(c.name == 'Giggle_Cages' for c in o.users_collection))):"

assert old_disc in text, "old_disc not found"
text = text.replace(old_disc, new_disc)

with open(INIT_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated discovery in __init__.py")
