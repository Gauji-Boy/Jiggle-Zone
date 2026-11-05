import os

init_path = r'd:\Blender\Giggle\giggle_addon\__init__.py'

with open(init_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update bl_info version
content = content.replace('"version": (1, 2, 0)', '"version": (1, 2, 1)', 1)

# 2. Add resolve_garment_target_zone and update resolve_clothing_target_zone
old_resolver_start = 'def resolve_clothing_target_zone(context):'
# We will define resolve_garment_target_zone before resolve_clothing_target_zone

new_resolver_code = '''def resolve_garment_target_zone(cloth_obj, body_obj, max_dist=0.35, ambiguity_thresh=0.05):
    """
    Spatially detect the closest Giggle physics zone on body_obj for a specific cloth_obj.
    Returns: (best_mod, best_vg, best_dist, status_code)
    status_code: 'OK', 'EXCEEDS_DISTANCE', 'AMBIGUOUS', 'NO_ZONES'
    """
    try:
        from mathutils import Vector
        mods = get_giggle_modifiers(body_obj)
        if not mods:
            return None, None, 999.0, 'NO_ZONES'

        c_center = sum((cloth_obj.matrix_world @ Vector(b) for b in cloth_obj.bound_box), start=Vector()) / 8.0

        candidates = []
        for m in mods:
            vg_name = get_mod_socket_attribute_name(m, 'Socket_2')
            if not vg_name or vg_name not in body_obj.vertex_groups:
                continue
            vg_idx = body_obj.vertex_groups[vg_name].index
            v_pts = [body_obj.matrix_world @ v.co for v in body_obj.data.vertices if any(g.group == vg_idx and g.weight > 0.1 for g in v.groups)]
            if v_pts:
                z_center = sum(v_pts, start=Vector()) / len(v_pts)
                dist = (z_center - c_center).length
                candidates.append((dist, m, vg_name))

        if not candidates:
            return None, None, 999.0, 'NO_ZONES'

        candidates.sort(key=lambda x: x[0])
        best_dist, best_mod, best_vg = candidates[0]

        if best_dist > max_dist:
            return best_mod, best_vg, best_dist, 'EXCEEDS_DISTANCE'

        if len(candidates) > 1:
            second_dist = candidates[1][0]
            if (second_dist - best_dist) < ambiguity_thresh:
                return best_mod, best_vg, best_dist, 'AMBIGUOUS'

        return best_mod, best_vg, best_dist, 'OK'
    except Exception as exc:
        print(f"[Giggle] Error resolving garment target zone: {exc}")
        return None, None, 999.0, 'ERROR'


def resolve_clothing_target_zone(context):
    """Detect the spatially closest Giggle physics zone for the active/first selected clothing."""
    try:
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
        body = context.active_object if context.active_object in giggle_bodies else (giggle_bodies[0] if giggle_bodies else None)
        if not body:
            for o in getattr(context.scene, 'objects', []):
                if o.type == 'MESH' and get_giggle_modifiers(o):
                    body = o
                    break
        if not body:
            return None, None, None, None

        clothing_objs = [o for o in selected_meshes if o != body]
        if not clothing_objs:
            mods = get_giggle_modifiers(body)
            if mods:
                return body, mods[0], get_mod_socket_attribute_name(mods[0], 'Socket_2'), None
            return None, None, None, None

        cloth = clothing_objs[0]
        mod, vg, dist, status = resolve_garment_target_zone(cloth, body)
        return body, mod, vg, dist
    except Exception:
        return None, None, None, None'''

assert old_resolver_start in content, "old_resolver_start not found!"

# Find old resolve_clothing_target_zone function end
old_func_end = 'def get_clothing_target_zone_items(self, context):'
assert old_func_end in content, "old_func_end not found!"

idx_start = content.index(old_resolver_start)
idx_end = content.index(old_func_end)

content = content[:idx_start] + new_resolver_code + '\n\n' + content[idx_end:]
print("Updated resolver functions!")

with open(init_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved __init__.py part 1")
