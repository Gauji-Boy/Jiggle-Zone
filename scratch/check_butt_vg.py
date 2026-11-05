import bpy

body = bpy.data.objects.get("kasumi_body")
vg_butt = body.vertex_groups.get("Butt_Zone")

vg_idx = vg_butt.index
butt_verts = [(v.index, g.weight, (body.matrix_world @ v.co)) for v in body.data.vertices for g in v.groups if g.group == vg_idx and g.weight > 0.1]

print(f"Butt_Zone has {len(butt_verts)} vertices with weight > 0.1")
z_coords = [p[2][2] for p in butt_verts]
print(f"Butt_Zone Z coordinates: min={min(z_coords):.3f}, max={max(z_coords):.3f}")

# Find any butt_zone vertex near the chest (Z > 1.0)
high_verts = [p for p in butt_verts if p[2][2] > 1.0]
print(f"Butt_Zone vertices with Z > 1.0 (chest level): {len(high_verts)}")
for v in high_verts[:5]:
    print(f"  vert {v[0]}: weight={v[1]:.3f}, co={v[2]}")
