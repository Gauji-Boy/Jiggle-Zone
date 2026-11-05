import bpy

proxy = bpy.data.objects.get("kasumi_body_Jiggle_Zone_Proxy")
body = bpy.data.objects.get("kasumi_body")

print(f"Proxy has {len(proxy.vertex_groups)} vertex groups.")
print(f"Body has {len(body.vertex_groups)} vertex groups.")

# Check deform weights on vert 0 of proxy vs vert 791 of body
print("Proxy vert 0 groups:", [(g.group, proxy.vertex_groups[g.group].name, g.weight) for g in proxy.data.vertices[0].groups])
print("Body vert 791 groups:", [(g.group, body.vertex_groups[g.group].name, g.weight) for g in body.data.vertices[791].groups])

# Check Armature modifier on proxy
arm_mod = next((m for m in proxy.modifiers if m.type == 'ARMATURE'), None)
print(f"Proxy Armature modifier: object={getattr(arm_mod, 'object', None)}, show_viewport={arm_mod.show_viewport}")
