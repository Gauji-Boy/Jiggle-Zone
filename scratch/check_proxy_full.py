import bpy

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

bpy.ops.object.select_all(action='DESELECT')
top.select_set(True)
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.giggle.attach_clothing_proxy()

proxy = bpy.data.objects.get("kasumi_body_Jiggle_Zone_Proxy")

print(f"Proxy has {len(proxy.vertex_groups)} vertex groups.")
print(f"Body has {len(body.vertex_groups)} vertex groups.")

print("Proxy vert 0 groups:", [(g.group, proxy.vertex_groups[g.group].name, round(g.weight, 4)) for g in proxy.data.vertices[0].groups])
print("Body vert 791 groups:", [(g.group, body.vertex_groups[g.group].name, round(g.weight, 4)) for g in body.data.vertices[791].groups])

arm_mod = next((m for m in proxy.modifiers if m.type == 'ARMATURE'), None)
print(f"Proxy Armature modifier: object={getattr(arm_mod, 'object', None)}, show_viewport={arm_mod.show_viewport}")

# Let's test evaluating proxy alone
dg = bpy.context.evaluated_depsgraph_get()
p_eval = proxy.evaluated_get(dg)
print("Proxy vert 0 evaluated at frame 1:", p_eval.matrix_world @ p_eval.data.vertices[0].co)

# Check frame 2
bpy.context.scene.frame_set(2)
dg = bpy.context.evaluated_depsgraph_get()
p_eval = proxy.evaluated_get(dg)
print("Proxy vert 0 evaluated at frame 2:", p_eval.matrix_world @ p_eval.data.vertices[0].co)
