import bpy
from giggle_addon import get_giggle_modifiers, get_mod_socket_attribute_name

body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

mods = get_giggle_modifiers(body)
candidates = []
for m in mods:
    vg_name = get_mod_socket_attribute_name(m, 'Socket_2')
    vg_idx = body.vertex_groups[vg_name].index
    v_pts = [body.matrix_world @ v.co for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.1 for g in v.groups)]
    
    n_c = len(top.data.vertices)
    step_c = max(1, n_c // 60)
    c_pts = [top.matrix_world @ top.data.vertices[i].co for i in range(0, n_c, step_c)]
    
    step_z = max(1, len(v_pts) // 60)
    z_pts = v_pts[::step_z]
    surf_dist = min((p_c - p_z).length for p_c in c_pts for p_z in z_pts)
    candidates.append((surf_dist, m.name, vg_name))

print("Candidates:", candidates)
