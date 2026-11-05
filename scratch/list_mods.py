import bpy

body = bpy.data.objects.get('kasumi_body')
for i, m in enumerate(body.modifiers):
    print(f"Index {i}: {m.name} ({m.type}), show_viewport={m.show_viewport}")
