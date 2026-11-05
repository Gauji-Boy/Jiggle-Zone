import os

file_path = "d:/Blender/Giggle/giggle_addon/__init__.py"
with open(file_path, "r", encoding="utf-8", newline="") as f:
    text = f.read()

# Verify initial clean state
assert "\r\r\n" not in text, "File contains double carriage returns!"
print(f"Read {len(text.splitlines())} lines from __init__.py")

# 1. Update resolve_garment_target_zone
old_resolve = """def resolve_garment_target_zone(cloth_obj, body_obj, max_dist=0.35, ambiguity_thresh=0.05):
    \"\"\"
    Spatially detect the closest Giggle physics zone on body_obj for a specific cloth_obj.
    Returns: (best_mod, best_vg, best_dist, status_code)
    status_code: 'OK', 'EXCEEDS_DISTANCE', 'AMBIGUOUS', 'NO_ZONES'
    \"\"\"
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
        print(f\"[Giggle] Error resolving garment target zone: {exc}\")
        return None, None, 999.0, 'ERROR'"""

new_resolve = """def resolve_garment_target_zone(cloth_obj, body_obj, max_dist=0.35, ambiguity_thresh=0.05):
    \"\"\"
    Spatially detect the closest Giggle physics zone on body_obj for a specific cloth_obj.
    Uses geometry-aware surface proximity and character scale awareness.
    Returns: (best_mod, best_vg, best_dist, status_code)
    status_code: 'OK', 'EXCEEDS_DISTANCE', 'AMBIGUOUS', 'NO_ZONES', 'ERROR'
    \"\"\"
    try:
        from mathutils import Vector
        mods = get_giggle_modifiers(body_obj)
        if not mods:
            return None, None, 999.0, 'NO_ZONES'

        # Scale awareness based on character height / body dimensions
        body_h = max(body_obj.dimensions.z, 0.1)
        scale_fac = max(0.1, body_h / 1.7)
        eff_max_dist = max_dist * scale_fac
        eff_ambiguity = ambiguity_thresh * scale_fac

        # Sample cloth vertices for geometry-aware surface-to-surface proximity
        n_c = len(cloth_obj.data.vertices)
        if n_c == 0:
            return None, None, 999.0, 'ERROR'
        step_c = max(1, n_c // 60)
        c_pts = [cloth_obj.matrix_world @ cloth_obj.data.vertices[i].co for i in range(0, n_c, step_c)]

        candidates = []
        for m in mods:
            vg_name = get_mod_socket_attribute_name(m, 'Socket_2')
            if not vg_name or vg_name not in body_obj.vertex_groups:
                continue
            vg_idx = body_obj.vertex_groups[vg_name].index
            v_pts = [body_obj.matrix_world @ v.co for v in body_obj.data.vertices if any(g.group == vg_idx and g.weight > 0.1 for g in v.groups)]
            if v_pts:
                step_z = max(1, len(v_pts) // 60)
                z_pts = v_pts[::step_z]
                # Geometry-aware minimum surface-to-surface distance
                surf_dist = min((p_c - p_z).length for p_c in c_pts for p_z in z_pts)
                candidates.append((surf_dist, m, vg_name))

        if not candidates:
            return None, None, 999.0, 'NO_ZONES'

        candidates.sort(key=lambda x: x[0])
        best_dist, best_mod, best_vg = candidates[0]

        if best_dist > eff_max_dist:
            return best_mod, best_vg, best_dist, 'EXCEEDS_DISTANCE'

        if len(candidates) > 1:
            second_dist = candidates[1][0]
            ratio = second_dist / max(best_dist, 0.001)
            if (second_dist - best_dist) < eff_ambiguity and ratio < 2.0:
                return best_mod, best_vg, best_dist, 'AMBIGUOUS'

        return best_mod, best_vg, best_dist, 'OK'
    except Exception as exc:
        print(f\"[Giggle] Error resolving garment target zone: {exc}\")
        return None, None, 999.0, 'ERROR'"""

# Normalize CR-LF
old_resolve_crlf = old_resolve.replace("\n", "\r\n")
new_resolve_crlf = new_resolve.replace("\n", "\r\n")

assert old_resolve_crlf in text, "Could not find old_resolve in text!"
text = text.replace(old_resolve_crlf, new_resolve_crlf)
print("Updated resolve_garment_target_zone")

# 2. Update GIGGLE_OT_attach_clothing_proxy
start_marker = "class GIGGLE_OT_attach_clothing_proxy(Operator):"
end_marker = "class GIGGLE_OT_copy_zone_to_clothing(Operator):"

start_idx = text.find(start_marker)
end_idx = text.find(end_marker)
assert start_idx != -1 and end_idx != -1, "Could not find GIGGLE_OT_attach_clothing_proxy boundaries!"

new_operator = """class GIGGLE_OT_attach_clothing_proxy(Operator):
    \"\"\"Attach selected clothes to body jiggle using a clean non-destructive Deform Proxy (100% flush, transactional)\"\"\"
    bl_idname = "giggle.attach_clothing_proxy"
    bl_label = "Attach Clothes to Jiggle (Flush Surface)"
    bl_description = "Creates/reuses a clean manifold jiggle proxy and transactionally binds clothes with Surface Deform"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        has_giggle = any(get_giggle_modifiers(o) for o in selected_meshes)
        return len(selected_meshes) >= 2 and has_giggle

    def execute(self, context):
        import bmesh
        from mathutils import Vector
        scene = context.scene
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
        if not giggle_bodies:
            self.report({'WARNING'}, "No selected mesh has Giggle physics. Select your character body and clothing.")
            return {'CANCELLED'}

        active_obj = context.active_object if context.active_object in giggle_bodies else giggle_bodies[0]
        clothing_objs = [o for o in selected_meshes if o != active_obj]
        if not clothing_objs:
            self.report({'WARNING'}, "No clothing meshes selected. Select both clothing and character body.")
            return {'CANCELLED'}

        settings = getattr(scene, 'giggle_settings', None)
        target_choice = getattr(settings, 'clothing_target_zone', 'AUTO') if settings else 'AUTO'
        body_mods = get_giggle_modifiers(active_obj)

        # 1. Resolve target zone for EACH clothing mesh independently
        garment_zones = {}
        for cloth in clothing_objs:
            if target_choice != 'AUTO':
                matched_mod = next((m for m in body_mods if m.name == target_choice), None)
                if not matched_mod:
                    self.report({'ERROR'}, f"Selected manual zone '{target_choice}' not found on '{active_obj.name}'.")
                    return {'CANCELLED'}
                matched_vg = get_mod_socket_attribute_name(matched_mod, 'Socket_2')
                if not matched_vg or matched_vg not in active_obj.vertex_groups:
                    self.report({'ERROR'}, f"Zone '{matched_mod.name}' has no valid vertex group assigned.")
                    return {'CANCELLED'}
                garment_zones[cloth] = (matched_mod, matched_vg)
            else:
                best_mod, best_vg, dist, status = resolve_garment_target_zone(cloth, active_obj)
                if status == 'EXCEEDS_DISTANCE':
                    self.report({'ERROR'}, f"Garment '{cloth.name}' is {dist*100:.1f} cm away from the nearest jiggle zone. Select target zone explicitly.")
                    return {'CANCELLED'}
                elif status == 'AMBIGUOUS':
                    self.report({'ERROR'}, f"Garment '{cloth.name}' is ambiguous (equally close to multiple zones). Select target zone explicitly.")
                    return {'CANCELLED'}
                elif status != 'OK' or not best_mod:
                    self.report({'ERROR'}, f"Could not auto-detect a valid jiggle zone for '{cloth.name}'. Select target zone explicitly.")
                    return {'CANCELLED'}
                garment_zones[cloth] = (best_mod, best_vg)

        # 2. Group clothes by (src_mod, vg_name)
        zone_groups = {}
        for cloth, (m, vg) in garment_zones.items():
            zone_groups.setdefault((m, vg), []).append(cloth)

        # 3. State capture (Medium 10 & Medium 9)
        orig_mode = context.mode
        orig_frame = scene.frame_current
        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]

        # Switch to OBJECT mode defensively if needed
        if orig_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        # Tracking for full ACID transactional rollback (Critical 1, 2, 3)
        created_temp_proxies = []  # dicts: {'obj': tmp_proxy, 'mesh': proxy_data, 'perm_name': perm_name}
        staged_modifiers = []      # (cloth, staged_sd)
        orig_proxy_vis = {}        # proxy -> (hide_viewport, hide_get, hide_render)
        migrated_dependents = []   # (dep_obj, dep_mod, old_perm)
        bound_count = 0

        # Dedicated hidden collection for proxies to prevent viewport clutter / wire cage display
        giggle_col = bpy.data.collections.get("Giggle_Proxies")
        if not giggle_col:
            giggle_col = bpy.data.collections.new("Giggle_Proxies")
            scene.collection.children.link(giggle_col)

        try:
            try:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            except Exception:
                pass

            # Bind strictly at scene.frame_start
            scene.frame_set(scene.frame_start)
            dg = context.evaluated_depsgraph_get()
            dg.update()

            # Process each zone group
            for (src_mod, vg_name), clothes_in_zone in zone_groups.items():
                vg_idx = active_obj.vertex_groups[vg_name].index
                perm_name = f"{active_obj.name}_{vg_name}_Proxy"
                existing_proxy = bpy.data.objects.get(perm_name)

                can_reuse = False
                if existing_proxy and existing_proxy.type == 'MESH':
                    orig_proxy_vis[existing_proxy] = (existing_proxy.hide_viewport, existing_proxy.hide_get(), existing_proxy.hide_render)
                    has_verts = len(existing_proxy.data.vertices) > 0
                    body_arm_obj = getattr(next((m for m in active_obj.modifiers if m.type == 'ARMATURE'), None), 'object', None)
                    has_arm = any(m.type == 'ARMATURE' and m.object == body_arm_obj for m in existing_proxy.modifiers)
                    has_wiggy = any(m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for m in existing_proxy.modifiers)

                    # Robust Fingerprint Validation (High 4)
                    match_body = existing_proxy.get('_giggle_source_body') == active_obj.name
                    match_verts = existing_proxy.get('_giggle_source_verts') == len(active_obj.data.vertices)
                    match_vg = existing_proxy.get('_giggle_vg_name') == vg_name

                    if has_verts and has_arm and has_wiggy and match_body and match_verts and match_vg:
                        can_reuse = True

                if can_reuse:
                    target_proxy = existing_proxy
                    target_proxy.display_type = 'TEXTURED'
                    target_proxy.hide_viewport = False
                    target_proxy.hide_set(False)
                else:
                    tmp_proxy_name = f"_tmp_{active_obj.name}_{vg_name}_Proxy"
                    old_tmp = bpy.data.objects.get(tmp_proxy_name)
                    if old_tmp:
                        bpy.data.objects.remove(old_tmp, do_unlink=True)

                    proxy_data = active_obj.data.copy()
                    proxy_data.name = f"{tmp_proxy_name}_Mesh"
                    tmp_proxy = bpy.data.objects.new(tmp_proxy_name, proxy_data)
                    giggle_col.objects.link(tmp_proxy)
                    tmp_proxy.matrix_world = active_obj.matrix_world

                    # CRITICAL 2: Track immediately upon creation before any subsequent operation can throw!
                    proxy_record = {'obj': tmp_proxy, 'mesh': proxy_data, 'perm_name': perm_name}
                    created_temp_proxies.append(proxy_record)

                    # Extract zone vertices with 1 edge-ring dilation
                    bm = bmesh.new()
                    bm.from_mesh(proxy_data)
                    dvert_lay = bm.verts.layers.deform.active

                    verts_to_keep = set()
                    for v in bm.verts:
                        dvert = v[dvert_lay] if dvert_lay else None
                        w = dvert.get(vg_idx, 0.0) if dvert else 0.0
                        if w >= 0.01:
                            verts_to_keep.add(v)

                    dilated = set(verts_to_keep)
                    for v in verts_to_keep:
                        for e in v.link_edges:
                            dilated.add(e.other_vert(v))

                    verts_to_delete = [v for v in bm.verts if v not in dilated]
                    bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')

                    bad_edges = [e for e in bm.edges if len(e.link_faces) > 2 or e.is_wire]
                    if bad_edges:
                        bmesh.ops.delete(bm, geom=bad_edges, context='EDGES')

                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
                    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

                    bm.to_mesh(proxy_data)
                    proxy_data.update()
                    bm.free()

                    if len(tmp_proxy.data.vertices) == 0 or len(tmp_proxy.data.polygons) == 0:
                        raise RuntimeError(f"Proxy mesh for '{vg_name}' is empty. Check vertex group weights.")

                    # Defensive vertex group validation
                    for vg in active_obj.vertex_groups:
                        if vg.name not in tmp_proxy.vertex_groups:
                            tmp_proxy.vertex_groups.new(name=vg.name)

                    # Copy Armature and Giggle modifier to proxy
                    tmp_proxy.modifiers.clear()
                    for m in active_obj.modifiers:
                        if m.type == 'ARMATURE':
                            arm = tmp_proxy.modifiers.new(name=m.name, type='ARMATURE')
                            arm.object = m.object
                            for prop in ['use_vertex_groups', 'use_bone_envelopes', 'use_deform_delay']:
                                if hasattr(m, prop):
                                    setattr(arm, prop, getattr(m, prop))
                        elif m == src_mod:
                            g_mod = tmp_proxy.modifiers.new(name=m.name, type='NODES')
                            g_mod.node_group = m.node_group
                            if hasattr(m, "properties") and hasattr(m.properties, "inputs"):
                                for k in m.properties.inputs.keys():
                                    s_src = getattr(m.properties.inputs, k)
                                    s_dst = getattr(g_mod.properties.inputs, k, None)
                                    if s_dst:
                                        if getattr(s_src, 'attribute_name', None):
                                            s_dst.type = 'ATTRIBUTE'
                                            s_dst.attribute_name = s_src.attribute_name
                                        elif getattr(s_src, 'value', None) is not None:
                                            s_dst.type = 'VALUE'
                                            try:
                                                s_dst.value = s_src.value
                                            except Exception:
                                                pass

                    # Store proxy metadata & fingerprint properties (High 4)
                    tmp_proxy['_giggle_source_body'] = active_obj.name
                    tmp_proxy['_giggle_source_verts'] = len(active_obj.data.vertices)
                    tmp_proxy['_giggle_vg_name'] = vg_name
                    tmp_proxy['_giggle_proxy'] = True

                    # Normal display instead of WIRE to eliminate black wire cages when unhidden
                    tmp_proxy.display_type = 'TEXTURED'
                    tmp_proxy.hide_viewport = False
                    tmp_proxy.hide_set(False)
                    tmp_proxy.hide_render = True

                    target_proxy = tmp_proxy

                # Stage SurfaceDeform on each clothing item in this zone
                for cloth in clothes_in_zone:
                    staged_sd = cloth.modifiers.new(name="_tmp_Giggle_SurfaceDeform", type='SURFACE_DEFORM')
                    staged_sd.target = target_proxy
                    staged_sd.falloff = 4.0
                    staged_modifiers.append((cloth, staged_sd))

                    arm_idx = -1
                    for idx_m, m in enumerate(cloth.modifiers):
                        if m.type == 'ARMATURE':
                            arm_idx = idx_m
                    if arm_idx >= 0 and arm_idx + 1 < len(cloth.modifiers):
                        with context.temp_override(active_object=cloth, object=cloth):
                            try:
                                bpy.ops.object.modifier_move_to_index(modifier=staged_sd.name, index=arm_idx + 1)
                            except Exception:
                                pass

                    context.view_layer.objects.active = cloth
                    with context.temp_override(active_object=cloth, object=cloth):
                        bpy.ops.object.surfacedeform_bind(modifier=staged_sd.name)
                        if not staged_sd.is_bound:
                            raise RuntimeError(f"Surface Deform failed to bind on '{cloth.name}'. Target mesh violates deformation rules.")
                        bound_count += 1

            # ==================================================================
            # 4. COMMIT PHASE (Critical 1 & Critical 3: Dependent verification)
            # ==================================================================
            old_proxies_to_remove = []

            for p_info in created_temp_proxies:
                tmp_proxy = p_info['obj']
                perm_name = p_info['perm_name']
                old_perm = bpy.data.objects.get(perm_name)

                if old_perm and old_perm != tmp_proxy:
                    # Collect all external dependent objects targeting old_perm
                    dependent_mods = []
                    for obj in bpy.data.objects:
                        if obj not in clothing_objs and obj.type == 'MESH':
                            for m in obj.modifiers:
                                if m.type == 'SURFACE_DEFORM' and m.target == old_perm and getattr(m, 'is_bound', False):
                                    dependent_mods.append((obj, m))

                    # Rebind each dependent garment to tmp_proxy and verify is_bound == True
                    for dep_obj, dep_mod in dependent_mods:
                        dep_mod.target = tmp_proxy
                        context.view_layer.objects.active = dep_obj
                        with context.temp_override(active_object=dep_obj, object=dep_obj):
                            try:
                                bpy.ops.object.surfacedeform_bind(modifier=dep_mod.name)
                            except Exception as exc:
                                print(f"[Giggle] Migration bind failed on '{dep_obj.name}': {exc}")

                        if not dep_mod.is_bound:
                            # Revert migrated dependents back to old_perm
                            for r_obj, r_mod, _ in migrated_dependents:
                                r_mod.target = old_perm
                                with context.temp_override(active_object=r_obj, object=r_obj):
                                    try:
                                        bpy.ops.object.surfacedeform_bind(modifier=r_mod.name)
                                    except Exception:
                                        pass
                            raise RuntimeError(f"Dependent garment '{dep_obj.name}' failed to rebind to replacement proxy. Preserving old proxy.")

                        migrated_dependents.append((dep_obj, dep_mod, old_perm))

                    old_proxies_to_remove.append(old_perm)

            # Safely remove replaced proxies only after 100% of dependents verified
            for old_p in old_proxies_to_remove:
                bpy.data.objects.remove(old_p, do_unlink=True)

            # Finalize new proxies
            for p_info in created_temp_proxies:
                tmp_p = p_info['obj']
                tmp_p.name = p_info['perm_name']
                tmp_p.data.name = f"{tmp_p.name}_Mesh"
                tmp_p.display_type = 'TEXTURED'
                tmp_p.hide_viewport = True
                tmp_p.hide_set(True)
                tmp_p.hide_render = True

            # Finalize reused proxies
            for p in orig_proxy_vis.keys():
                if p and p.name in bpy.data.objects:
                    p.display_type = 'TEXTURED'
                    p.hide_viewport = True
                    p.hide_set(True)
                    p.hide_render = True

            # Hide dedicated proxies collection
            if giggle_col:
                giggle_col.hide_viewport = True
                giggle_col.hide_render = True

            # Finalize staged modifiers (Selective cleanup - Medium 8)
            for cloth, staged_sd in staged_modifiers:
                for m in list(cloth.modifiers):
                    if m == staged_sd:
                        continue
                    if m.type == 'NODES' and m.name.startswith("Giggle_") and m.name.endswith("_Follow"):
                        cloth.modifiers.remove(m)
                    elif m.type == 'SURFACE_DEFORM' and m.name == "Giggle_SurfaceDeform":
                        cloth.modifiers.remove(m)
                staged_sd.name = "Giggle_SurfaceDeform"

            self.report({'INFO'}, f"Successfully attached {bound_count} clothing mesh(es) to Giggle jiggle zones!")
            return {'FINISHED'}

        except Exception as e:
            # 5. TRANSACTIONAL ROLLBACK (Critical 1, 2, 3 & Medium 9)
            for cloth, staged_sd in staged_modifiers:
                if cloth and staged_sd.name in cloth.modifiers:
                    cloth.modifiers.remove(staged_sd)

            # Revert any migrated dependents back to their old proxies
            for dep_obj, dep_mod, old_perm in migrated_dependents:
                if dep_obj and dep_mod.name in dep_obj.modifiers and old_perm and old_perm.name in bpy.data.objects:
                    dep_mod.target = old_perm
                    with context.temp_override(active_object=dep_obj, object=dep_obj):
                        try:
                            bpy.ops.object.surfacedeform_bind(modifier=dep_mod.name)
                        except Exception:
                            pass

            # Remove all created temp proxies and their mesh datablocks (Critical 2)
            for p_info in created_temp_proxies:
                obj = p_info.get('obj')
                mesh = p_info.get('mesh')
                if obj and obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                if mesh and mesh.name in bpy.data.meshes:
                    bpy.data.meshes.remove(mesh, do_unlink=True)

            # Restore reused proxy visibility (Medium 9)
            for p, (hv, hg, hr) in orig_proxy_vis.items():
                if p and p.name in bpy.data.objects:
                    p.hide_viewport = hv
                    p.hide_set(hg)
                    p.hide_render = hr

            self.report({'ERROR'}, f"Clothing attachment failed (Rolled back): {e}")
            return {'CANCELLED'}

        finally:
            scene.frame_set(orig_frame)
            if orig_active and orig_active.name in bpy.data.objects:
                context.view_layer.objects.active = orig_active
            for o in orig_selected:
                if o and o.name in bpy.data.objects:
                    try:
                        o.select_set(True)
                    except Exception:
                        pass
            # Restore original context mode (Medium 10)
            if orig_mode != 'OBJECT' and orig_active and orig_active.name in bpy.data.objects:
                with context.temp_override(active_object=orig_active, object=orig_active):
                    try:
                        bpy.ops.object.mode_set(mode=orig_mode)
                    except Exception:
                        pass
"""

new_operator_crlf = new_operator.replace("\n", "\r\n")
text = text[:start_idx] + new_operator_crlf + "\r\n\r\n\r\n" + text[end_idx:]
print("Updated GIGGLE_OT_attach_clothing_proxy")

# 3. Update UI Multi-Garment Preview (Medium 7)
old_ui = """                    body, resolved_mod, resolved_vg, dist = resolve_clothing_target_zone(context)
                    if resolved_mod and resolved_vg:
                        dist_str = f" ({dist*100:.1f} cm)" if dist is not None else ""
                        if dist is not None and dist > 0.35:
                            col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='ERROR')
                        else:
                            col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='CHECKMARK')
                    else:
                        col.label(text="Auto: Each garment resolves closest zone", icon='INFO')"""

new_ui = """                    selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
                    giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
                    body = context.active_object if context.active_object in giggle_bodies else (giggle_bodies[0] if giggle_bodies else None)
                    clothing_objs = [o for o in selected_meshes if o != body]
                    if len(clothing_objs) > 1 and body:
                        col.label(text=f"Auto: {len(clothing_objs)} garments (resolving per-mesh):", icon='INFO')
                        for c in clothing_objs[:3]:
                            r_mod, r_vg, d_val, status = resolve_garment_target_zone(c, body)
                            if r_mod and r_vg:
                                d_s = f" ({d_val*100:.1f} cm)" if d_val is not None else ""
                                ic = 'CHECKMARK' if status == 'OK' else 'ERROR'
                                col.label(text=f"  • {c.name}: {r_mod.name}{d_s}", icon=ic)
                        if len(clothing_objs) > 3:
                            col.label(text=f"  ...and {len(clothing_objs)-3} more", icon='BLANK1')
                    else:
                        body_res, resolved_mod, resolved_vg, dist = resolve_clothing_target_zone(context)
                        if resolved_mod and resolved_vg:
                            dist_str = f" ({dist*100:.1f} cm)" if dist is not None else ""
                            if dist is not None and dist > 0.35:
                                col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='ERROR')
                            else:
                                col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='CHECKMARK')
                        else:
                            col.label(text="Auto: Each garment resolves closest zone", icon='INFO')"""

old_ui_crlf = old_ui.replace("\n", "\r\n")
new_ui_crlf = new_ui.replace("\n", "\r\n")

if old_ui_crlf in text:
    text = text.replace(old_ui_crlf, new_ui_crlf)
    print("Updated UI Multi-Garment Preview")

# Write back
with open(file_path, "w", encoding="utf-8", newline="") as f:
    f.write(text)

final_lines = len(text.splitlines())
print(f"Update complete! Final line count: {final_lines}")
assert "\r\r\n" not in text, "File contains double carriage returns after update!"
assert final_lines < 6200, f"Line count unexpectedly large: {final_lines}"
