init_path = r'd:\Blender\Giggle\giggle_addon\__init__.py'

with open(init_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'class GIGGLE_OT_attach_clothing_proxy(Operator):'
end_marker = 'class GIGGLE_OT_copy_zone_to_clothing(Operator):'

assert start_marker in content, "start_marker not found!"
assert end_marker in content, "end_marker not found!"

idx_start = content.index(start_marker)
idx_end = content.index(end_marker)

new_operator_code = '''class GIGGLE_OT_attach_clothing_proxy(Operator):
    """Attach selected clothes to body jiggle using a clean non-destructive Deform Proxy (100% flush, transactional)"""
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
                    self.report({'ERROR'}, f"Garment '{cloth.name}' is {dist*100:.1f} cm away from the nearest jiggle zone (>35 cm limit). Select target zone explicitly.")
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

        # 3. State capture
        orig_frame = scene.frame_current
        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]

        # Tracking for rollback
        created_temp_proxies = []
        staged_modifiers = []
        bound_count = 0

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
                    has_verts = len(existing_proxy.data.vertices) > 0
                    has_arm = any(m.type == 'ARMATURE' and m.object == getattr(next((m for m in active_obj.modifiers if m.type == 'ARMATURE'), None), 'object', None) for m in existing_proxy.modifiers)
                    has_wiggy = any(m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for m in existing_proxy.modifiers)
                    if has_verts and has_arm and has_wiggy:
                        can_reuse = True

                if can_reuse:
                    target_proxy = existing_proxy
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
                    target_col = active_obj.users_collection[0] if active_obj.users_collection else scene.collection
                    target_col.objects.link(tmp_proxy)
                    tmp_proxy.matrix_world = active_obj.matrix_world

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

                    tmp_proxy.display_type = 'WIRE'
                    tmp_proxy.hide_viewport = False
                    tmp_proxy.hide_set(False)
                    tmp_proxy.hide_render = True
                    tmp_proxy['_giggle_proxy'] = True

                    target_proxy = tmp_proxy
                    created_temp_proxies.append((tmp_proxy, perm_name))

                # Stage SurfaceDeform on each clothing item in this zone
                for cloth in clothes_in_zone:
                    staged_sd = cloth.modifiers.new(name="_tmp_Giggle_SurfaceDeform", type='SURFACE_DEFORM')
                    staged_sd.target = target_proxy
                    staged_sd.interpolation_falloff = 4.0
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
            # 4. COMMIT PHASE (All garments and proxies validated and bound)
            # ==================================================================
            for tmp_proxy, perm_name in created_temp_proxies:
                old_perm = bpy.data.objects.get(perm_name)
                if old_perm and old_perm != tmp_proxy:
                    for obj in bpy.data.objects:
                        if obj not in clothing_objs:
                            for m in obj.modifiers:
                                if m.type == 'SURFACE_DEFORM' and m.target == old_perm:
                                    m.target = tmp_proxy
                                    with context.temp_override(active_object=obj, object=obj):
                                        try:
                                            bpy.ops.object.surfacedeform_bind(modifier=m.name)
                                        except Exception:
                                            pass
                    bpy.data.objects.remove(old_perm, do_unlink=True)
                tmp_proxy.name = perm_name
                tmp_proxy.hide_viewport = True
                tmp_proxy.hide_set(True)
                tmp_proxy.hide_render = True

            for (src_mod, vg_name) in zone_groups.keys():
                perm_name = f"{active_obj.name}_{vg_name}_Proxy"
                p = bpy.data.objects.get(perm_name)
                if p:
                    p.hide_viewport = True
                    p.hide_set(True)
                    p.hide_render = True

            for cloth, staged_sd in staged_modifiers:
                for m in list(cloth.modifiers):
                    if m == staged_sd:
                        continue
                    if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1':
                        cloth.modifiers.remove(m)
                    elif m.type == 'SURFACE_DEFORM' and m.name == "Giggle_SurfaceDeform":
                        cloth.modifiers.remove(m)
                staged_sd.name = "Giggle_SurfaceDeform"

            self.report({'INFO'}, f"Successfully attached {bound_count} clothing mesh(es) to Giggle jiggle zones!")
            return {'FINISHED'}

        except Exception as e:
            # 5. TRANSACTIONAL ROLLBACK
            for cloth, staged_sd in staged_modifiers:
                if cloth and staged_sd.name in cloth.modifiers:
                    cloth.modifiers.remove(staged_sd)

            for tmp_proxy, _ in created_temp_proxies:
                if tmp_proxy and tmp_proxy.name in bpy.data.objects:
                    bpy.data.objects.remove(tmp_proxy, do_unlink=True)

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


'''

content = content[:idx_start] + new_operator_code + content[idx_end:]

# Also update VIEW3D_PT_giggle_clothing_follower
ui_start = 'class VIEW3D_PT_giggle_clothing_follower(Panel):'
ui_end = 'class GIGGLE_OT_pin_hair_roots(Operator):'
assert ui_start in content
assert ui_end in content

idx_uistart = content.index(ui_start)
idx_uiend = content.index(ui_end)

new_ui_code = '''class VIEW3D_PT_giggle_clothing_follower(Panel):
    bl_label = "Clothing Follower & Deform"
    bl_idname = "VIEW3D_PT_giggle_clothing_follower"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Giggle'
    bl_order = 16
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        try:
            settings = getattr(context.scene, 'giggle_settings', None)
            box = layout.box()
            box.label(text="Make Clothing Follow Jiggle:", icon='MOD_CLOTH')

            if settings:
                col = box.column(align=True)
                col.prop(settings, "clothing_target_zone", text="Zone")
                if settings.clothing_target_zone != 'AUTO':
                    col.label(text=f"Target: {settings.clothing_target_zone} (Manual)", icon='RESTRICT_SELECT_OFF')
                else:
                    body, resolved_mod, resolved_vg, dist = resolve_clothing_target_zone(context)
                    if resolved_mod and resolved_vg:
                        dist_str = f" ({dist*100:.1f} cm)" if dist is not None else ""
                        if dist is not None and dist > 0.35:
                            col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='ERROR')
                        else:
                            col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='CHECKMARK')
                    else:
                        col.label(text="Auto: Each garment resolves closest zone", icon='INFO')

            box.operator("giggle.attach_clothing_proxy", text="Attach Clothes to Jiggle (Flush Surface)", icon='MOD_MESHDEFORM')

            box.separator()
            box.label(text="Clothing Deform Rebind:", icon='HOOK')
            box.operator("giggle.rebind_clothing_modifiers", text="Rebind Modifiers (Scene Start)", icon='FILE_REFRESH')

            box.separator()
            box.operator("giggle.copy_zone_to_clothing", text="Copy Physics Solver to Clothes (Advanced)", icon='DUPLICATE')
        except Exception as e:
            layout.label(text=f"UI Error: {e}", icon='ERROR')


'''

content = content[:idx_uistart] + new_ui_code + content[idx_uiend:]

with open(init_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved __init__.py part 2 successfully!")
