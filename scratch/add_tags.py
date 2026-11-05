with open(r'd:\Blender\Giggle\giggle_addon\__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

t = '        self.report({\'INFO\'}, f"Added Giggle Zone \'{mod.name}\' ({engine})")'
r = '''        obj.update_tag(eval_flags={'GEOMETRY'})
        try:
            context.view_layer.update()
        except Exception:
            pass
        self.report({'INFO'}, f"Added Giggle Zone '{mod.name}' ({engine})")'''
assert t in c, 't not found'
c = c.replace(t, r)

with open(r'd:\Blender\Giggle\giggle_addon\__init__.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Updated add_zone tag successfully!')
