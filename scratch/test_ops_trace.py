import bpy

# Load the file fresh
body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')
topcen = bpy.data.objects.get('topcen')

print("=== INITIAL STATE ===")
print("frame_current:", bpy.context.scene.frame_current)
print("body modifiers:", [m.name for m in body.modifiers])
print("body parent:", body.parent)

# Check if rest_position attribute exists
for attr in body.data.attributes:
    print(f"Attribute: {attr.name}, type: {attr.data_type}, domain: {attr.domain}")

# Let's check evaluated vertex 0 across frames before any operator
print("Before operator:")
for f in [0, 1, 2, 3]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    t_ev = topcen.evaluated_get(dg)
    print(f"Frame {f}: body v0={b_ev.data.vertices[0].co.z:.3f}, topcen v0={t_ev.data.vertices[0].co.z:.3f}")
