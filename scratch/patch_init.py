import os
import re

INIT_PATH = r"d:\Blender\Giggle\giggle_addon\__init__.py"

with open(INIT_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Imports at top
if "import hashlib" not in text:
    old_imp = "import json\nimport re"
    new_imp = "import json\nimport re\nimport hashlib\nimport shutil\nimport time"
    assert old_imp in text, "Could not find import insertion point"
    text = text.replace(old_imp, new_imp, 1)
    print("1. Added hashlib, shutil, time imports.")

# 2. Add check_cache_on_render to GiggleSceneSettings
if "check_cache_on_render:" not in text:
    old_setting = """    bake_disk_path: StringProperty(
        name="Bake Directory",
        description="Directory for external cache files",
        subtype='DIR_PATH',
        default="//giggle_cache/"
    )"""
    new_setting = """    bake_disk_path: StringProperty(
        name="Bake Directory",
        description="Directory for external cache files",
        subtype='DIR_PATH',
        default="//giggle_cache/"
    )
    check_cache_on_render: BoolProperty(
        name="Pre-Flight Render Check",
        description="Verify simulation caches match current animation and physics before rendering",
        default=True
    )"""
    assert old_setting in text, "Could not find GiggleSceneSettings insertion point"
    text = text.replace(old_setting, new_setting, 1)
    print("2. Added check_cache_on_render to GiggleSceneSettings.")

# 3. Replace baking helpers, validity checker, and operators
start_marker = "def get_giggle_simulation_objects(context, obj=None):"
end_marker = "class GIGGLE_OT_fix_gpu_subdivision(Operator):"

idx_start = text.find(start_marker)
idx_end = text.find(end_marker)
assert idx_start != -1 and idx_end != -1, "Could not find operator block markers"

new_baking_block = '''FINGERPRINT_SCHEMA = "2.0.0"


def get_action_fcurves(act):
    """Retrieve all F-Curves from an action, supporting both Blender 5.2/5.3 Layered Actions and legacy actions."""
    if not act:
        return []
    fcurves = []
    if hasattr(act, "layers") and act.layers:
        for layer in act.layers:
            for strip in getattr(layer, "strips", []):
                for cb in getattr(strip, "channelbags", []):
                    fcurves.extend(cb.fcurves)
    elif hasattr(act, "fcurves") and act.fcurves:
        fcurves.extend(act.fcurves)
    return fcurves


def get_driving_armature(cage_or_mesh):
    """Find the armature driving this simulation object or its source body."""
    if not cage_or_mesh:
        return None
    for m in getattr(cage_or_mesh, "modifiers", []):
        if m.type == 'ARMATURE' and m.object:
            return m.object
    if cage_or_mesh.parent and getattr(cage_or_mesh.parent, "type", "") == 'ARMATURE':
        return cage_or_mesh.parent
    src_body_name = cage_or_mesh.get('_giggle_source_body')
    if src_body_name:
        src_body = bpy.data.objects.get(src_body_name)
        if src_body:
            for m in getattr(src_body, "modifiers", []):
                if m.type == 'ARMATURE' and m.object:
                    return m.object
            if src_body.parent and getattr(src_body.parent, "type", "") == 'ARMATURE':
                return src_body.parent
    for o in bpy.data.objects:
        if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action:
            return o
    return None


def compute_animation_hash(arm_obj):
    """Deterministic hash of armature animation keyframes, handles, and interpolation."""
    if not arm_obj or not getattr(arm_obj, "animation_data", None):
        return "NO_ANIM"
    act = arm_obj.animation_data.action
    if not act:
        return "NO_ACTION"
    fcurves = get_action_fcurves(act)
    if not fcurves:
        return f"EMPTY_ACTION_{act.name}"
    h = hashlib.sha256()
    h.update(act.name.encode('utf-8'))
    sorted_fc = sorted(fcurves, key=lambda fc: (fc.data_path, fc.array_index))
    for fc in sorted_fc:
        h.update(f"{fc.data_path}[{fc.array_index}]".encode('utf-8'))
        for kp in fc.keyframe_points:
            entry = f"{round(kp.co[0], 3)}:{round(kp.co[1], 4)}:{round(kp.handle_left[0], 3)}:{round(kp.handle_left[1], 4)}:{round(kp.handle_right[0], 3)}:{round(kp.handle_right[1], 4)}:{kp.interpolation};"
            h.update(entry.encode('utf-8'))
    return h.hexdigest()


def compute_armature_hash(arm_obj):
    """Deterministic hash of armature bone rest transforms and constraints."""
    if not arm_obj or arm_obj.type != 'ARMATURE' or not arm_obj.data:
        return "NO_ARMATURE"
    h = hashlib.sha256()
    for b in sorted(arm_obj.data.bones, key=lambda x: x.name):
        h.update(b.name.encode('utf-8'))
        h.update(f"{b.head.x:.4f},{b.head.y:.4f},{b.head.z:.4f}".encode('utf-8'))
        h.update(f"{b.tail.x:.4f},{b.tail.y:.4f},{b.tail.z:.4f}".encode('utf-8'))
    if arm_obj.pose:
        for pb in sorted(arm_obj.pose.bones, key=lambda x: x.name):
            for c in pb.constraints:
                h.update(f"{pb.name}:{c.type}:{c.mute}:{getattr(c, 'influence', 1.0):.4f}".encode('utf-8'))
    return h.hexdigest()


def compute_physics_hash(cage_obj):
    """Deterministic hash of Giggle Wiggy GN modifier inputs."""
    if not cage_obj:
        return "NO_OBJ"
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod:
        return "NO_WIGGY_MOD"
    h = hashlib.sha256()
    s_in = getattr(getattr(mod, "properties", None), "inputs", None)
    if s_in:
        for identifier in sorted(dir(s_in)):
            if identifier.startswith("Socket_"):
                sock = getattr(s_in, identifier)
                val = getattr(sock, "value", None)
                if val is not None:
                    h.update(f"{identifier}={val};".encode('utf-8'))
                att = getattr(sock, "attribute_name", None)
                if att is not None:
                    h.update(f"{identifier}_att={att};".encode('utf-8'))
    return h.hexdigest()


def compute_geometry_hash(cage_obj):
    """Deterministic hash of cage mesh vertex count and rest vertex coordinates."""
    if not cage_obj or cage_obj.type != 'MESH' or not cage_obj.data:
        return "NO_GEOMETRY"
    h = hashlib.sha256()
    mesh = cage_obj.data
    h.update(f"vcount={len(mesh.vertices)};".encode('utf-8'))
    for v in mesh.vertices:
        h.update(f"{v.co.x:.4f},{v.co.y:.4f},{v.co.z:.4f};".encode('utf-8'))
    src_body_name = cage_obj.get('_giggle_source_body')
    vg_name = cage_obj.get('_giggle_vg_name')
    if src_body_name and vg_name:
        src_body = bpy.data.objects.get(src_body_name)
        if src_body and src_body.type == 'MESH' and src_body.data:
            vg = src_body.vertex_groups.get(vg_name)
            if vg:
                h.update(f"vg={vg_name};".encode('utf-8'))
                for v in src_body.data.vertices:
                    try:
                        w = vg.weight(v.index)
                        if w > 0.0001:
                            h.update(f"{v.index}:{w:.3f};".encode('utf-8'))
                    except Exception:
                        pass
    return h.hexdigest()


def compute_simulation_hash(scene, settings, storage_mode, f_start, f_end):
    """Deterministic hash of scene frame range, FPS, and storage mode."""
    h = hashlib.sha256()
    fps = round(scene.render.fps / scene.render.fps_base, 3) if scene.render.fps_base else scene.render.fps
    h.update(f"range={f_start}-{f_end};fps={fps};storage={storage_mode};".encode('utf-8'))
    return h.hexdigest()


def compute_zone_fingerprint(cage_or_mesh, context, storage_mode="PACKED", f_start=1, f_end=250):
    """Generate complete multi-domain cryptographic dependency fingerprint."""
    scene = context.scene
    arm = get_driving_armature(cage_or_mesh)
    return {
        "schema": FINGERPRINT_SCHEMA,
        "animation": compute_animation_hash(arm),
        "armature": compute_armature_hash(arm),
        "physics": compute_physics_hash(cage_or_mesh),
        "geometry": compute_geometry_hash(cage_or_mesh),
        "simulation": compute_simulation_hash(scene, None, storage_mode, f_start, f_end)
    }


def save_zone_bake_fingerprint(cage_or_mesh, context, storage_mode, f_start, f_end, fp_dict=None, is_valid=True, reason=""):
    """Stamp verified bake fingerprint and status metadata onto simulation object."""
    now = time.time()
    fp = fp_dict or compute_zone_fingerprint(cage_or_mesh, context, storage_mode, f_start, f_end)
    cage_or_mesh['_giggle_baked_at_timestamp'] = now
    cage_or_mesh['_giggle_bake_fingerprint_json'] = json.dumps(fp, sort_keys=True)
    cage_or_mesh['_giggle_bake_schema_version'] = FINGERPRINT_SCHEMA
    cage_or_mesh['_giggle_baked_frame_range'] = (f_start, f_end)
    cage_or_mesh['_giggle_baked_storage'] = storage_mode
    cage_or_mesh['_giggle_status'] = "BAKED" if is_valid else ("OUTDATED" if "modified" in reason.lower() else "FAILED")
    cage_or_mesh['_giggle_last_known_valid'] = is_valid
    cage_or_mesh['_giggle_outdated_reason'] = reason
    cage_or_mesh.pop('_giggle_settings_modified_at', None)


def get_giggle_simulation_objects(context, obj=None):
    """Return all Giggle-managed simulation objects (cages or character mesh if full-mesh)."""
    sim_objs = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and (o.get('_giggle_cage') or (o.users_collection and any(c.name == 'Giggle_Cages' for c in o.users_collection))):
            if any(m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for m in o.modifiers):
                if o not in sim_objs:
                    sim_objs.append(o)
    target = obj or context.active_object
    if target and target.type == 'MESH':
        full_mods = [m for m in get_giggle_modifiers(target) if m.show_viewport and not is_zone_in_cage_mode(target, m)]
        if full_mods and target not in sim_objs:
            sim_objs.append(target)
    return sim_objs


def get_cage_bake_status(cage_obj):
    """Fast check of cage bake status for UI display (zero heavy computation during redraw)."""
    if not cage_obj or cage_obj.type != 'MESH':
        return 'NOT_BAKED', (1, 250), 'PACKED', "Object is not a mesh"
    bake_time = cage_obj.get('_giggle_baked_at_timestamp', None)
    if not bake_time:
        return 'NOT_BAKED', (1, 250), 'PACKED', "Not baked"

    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod or not mod.bakes:
        return 'NOT_BAKED', (1, 250), 'PACKED', "Missing Wiggy modifier"

    has_data = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_data:
        return 'NOT_BAKED', (1, 250), 'PACKED', "No simulation cache blocks"

    frange = cage_obj.get('_giggle_baked_frame_range', (1, 250))
    storage = cage_obj.get('_giggle_baked_storage', 'PACKED')

    last_mod_time = cage_obj.get('_giggle_settings_modified_at', 0)
    if last_mod_time > bake_time:
        return 'OUTDATED', frange, storage, "Physics settings modified via Giggle UI"

    st = cage_obj.get('_giggle_status', None)
    reason = cage_obj.get('_giggle_outdated_reason', '')
    if st in ('BAKED', 'OUTDATED', 'FAILED'):
        return st, frange, storage, reason

    return 'BAKED', frange, storage, "Matches Setup"


def check_cage_validity(cage_obj, context):
    """On-demand cryptographic dependency verification for a simulation cage."""
    if not cage_obj or cage_obj.type != 'MESH':
        return 'NOT_BAKED', "Object is not a mesh"
    
    bake_time = cage_obj.get('_giggle_baked_at_timestamp', None)
    if not bake_time:
        cage_obj['_giggle_status'] = 'NOT_BAKED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Simulation not baked"
        return 'NOT_BAKED', "Simulation not baked"
    
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod or not mod.bakes:
        cage_obj['_giggle_status'] = 'NOT_BAKED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Missing Wiggy modifier or bake items"
        return 'NOT_BAKED', "Missing Wiggy modifier or bake items"
    
    has_data = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_data:
        cage_obj['_giggle_status'] = 'NOT_BAKED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "No simulation cache blocks present"
        return 'NOT_BAKED', "No simulation cache blocks present"
    
    fp_json = cage_obj.get('_giggle_bake_fingerprint_json', None)
    if not fp_json:
        if cage_obj.get('_giggle_settings_modified_at', 0) > bake_time:
            cage_obj['_giggle_status'] = 'OUTDATED'
            cage_obj['_giggle_last_known_valid'] = False
            cage_obj['_giggle_outdated_reason'] = "Physics settings modified"
            return 'OUTDATED', "Physics settings modified"
        cage_obj['_giggle_status'] = 'OUTDATED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Missing dependency fingerprint (baked with older version)"
        return 'OUTDATED', "Missing dependency fingerprint (baked with older version)"
    
    try:
        saved_fp = json.loads(fp_json)
    except Exception:
        cage_obj['_giggle_status'] = 'OUTDATED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Invalid fingerprint JSON"
        return 'OUTDATED', "Invalid fingerprint JSON"
    
    frange = cage_obj.get('_giggle_baked_frame_range', (context.scene.frame_start, context.scene.frame_end))
    storage = cage_obj.get('_giggle_baked_storage', 'PACKED')
    curr_fp = compute_zone_fingerprint(cage_obj, context, storage, frange[0], frange[1])
    
    status = 'BAKED'
    reason = "Cache matches setup"
    if saved_fp.get('animation') != curr_fp['animation']:
        status = 'OUTDATED'
        reason = "Animation keyframes or handles modified"
    elif saved_fp.get('physics') != curr_fp['physics']:
        status = 'OUTDATED'
        reason = "Physics settings modified"
    elif saved_fp.get('geometry') != curr_fp['geometry']:
        status = 'OUTDATED'
        reason = "Cage geometry or vertex weights modified"
    elif saved_fp.get('armature') != curr_fp['armature']:
        status = 'OUTDATED'
        reason = "Armature rest pose or rig constraints modified"
    elif saved_fp.get('simulation') != curr_fp['simulation']:
        status = 'OUTDATED'
        reason = "Frame range, FPS, or storage mode modified"
        
    cage_obj['_giggle_status'] = status
    cage_obj['_giggle_last_known_valid'] = (status == 'BAKED')
    cage_obj['_giggle_outdated_reason'] = reason
    return status, reason


def preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end):
    """Run pre-bake validation checks before touching existing caches."""
    if not sim_objs:
        return False, "No active Giggle simulation zones found."
    if storage_mode == 'DISK' and not bpy.data.is_saved:
        return False, "Please save your .blend file before baking to external disk."
    if f_end < f_start:
        return False, f"Invalid frame range: start frame ({f_start}) > end frame ({f_end})."
    if getattr(getattr(context, 'screen', None), 'is_animation_playing', False):
        return False, "Cannot bake while animation playback is running."
    
    for o in sim_objs:
        for m in o.modifiers:
            if m.type == 'NODES' and m.node_group and m.node_group.name != 'Wiggy 0.1':
                if any(node.type == 'SIMULATION_OUTPUT' for node in getattr(m.node_group, 'nodes', [])):
                    return False, f"Conflicting non-Giggle simulation modifier found on '{o.name}'. Aborting to protect unrelated simulations."
    return True, "Preflight passed"


def create_project_backup():
    """Create a recoverable copy of the saved .blend file before cache modification."""
    if not bpy.data.is_saved:
        return None
    try:
        filepath = bpy.data.filepath
        if not filepath or not os.path.exists(filepath):
            return None
        backup_dir = os.path.join(os.path.dirname(filepath), "giggle_backup")
        os.makedirs(backup_dir, exist_ok=True)
        basename = os.path.basename(filepath)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{basename}.{timestamp}.bak")
        shutil.copy2(filepath, backup_path)
        return backup_path
    except Exception as e:
        print(f"[Giggle Backup Warning] Could not create backup copy: {e}")
        return None


def execute_cage_bake_step(cage_obj, context, storage_mode, disk_path, f_start, f_end):
    """Bake a single simulation cage individually with full verification and fingerprinting."""
    pre_fp = compute_zone_fingerprint(cage_obj, context, storage_mode, f_start, f_end)

    try:
        with context.temp_override(active_object=cage_obj, selected_objects=[cage_obj]):
            bpy.ops.object.simulation_nodes_cache_delete(selected=True)
    except Exception:
        pass

    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod:
        return False, "Missing Wiggy 0.1 simulation modifier"

    mod.bake_target = storage_mode
    if storage_mode == 'DISK':
        mod.bake_directory = disk_path
    for b in mod.bakes:
        b.frame_start = f_start
        b.frame_end = f_end

    for ob in bpy.data.objects:
        ob.select_set(False)
    cage_obj.select_set(True)
    context.view_layer.objects.active = cage_obj

    context.scene.frame_set(f_start)
    context.view_layer.update()

    with context.temp_override(active_object=cage_obj, selected_objects=[cage_obj]):
        bake_res = bpy.ops.object.simulation_nodes_cache_bake(selected=True)

    if bake_res != {'FINISHED'}:
        cage_obj['_giggle_status'] = 'FAILED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = f"Blender bake operator returned {bake_res}"
        return False, f"Blender bake operator returned {bake_res}"

    has_blocks = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_blocks:
        cage_obj['_giggle_status'] = 'FAILED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Bake produced 0 simulation cache blocks"
        return False, "Bake produced 0 simulation cache blocks"

    post_fp = compute_zone_fingerprint(cage_obj, context, storage_mode, f_start, f_end)
    if pre_fp != post_fp:
        save_zone_bake_fingerprint(cage_obj, context, storage_mode, f_start, f_end, fp_dict=post_fp, is_valid=False, reason="Dependencies modified during baking")
        return False, "Dependencies modified during baking"

    save_zone_bake_fingerprint(cage_obj, context, storage_mode, f_start, f_end, fp_dict=post_fp, is_valid=True, reason="")
    return True, "Success"


class GIGGLE_OT_bake_all_cages(Operator):
    """Bake simulation caches for all active Giggle cages (or active full-mesh zones)"""
    bl_idname = "giggle.bake_all_cages"
    bl_label = "Bake All Giggle Zones"
    bl_description = "Bake every active Giggle physics simulation for non-sequential, instantaneous playback"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def execute(self, context):
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        disk_path = getattr(settings, 'bake_disk_path', '//giggle_cache/') if settings else '//giggle_cache/'
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        sim_objs = get_giggle_simulation_objects(context)
        ok, msg = preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        succeeded = []
        failed = []

        try:
            for o in sim_objs:
                ok_bake, err = execute_cage_bake_step(o, context, storage_mode, disk_path, f_start, f_end)
                if ok_bake:
                    succeeded.append(o)
                else:
                    failed.append((o, err))

            if failed and not succeeded:
                self.report({'ERROR'}, f"Bake failed for all {len(sim_objs)} zone(s). Check simulation ranges.")
                return {'CANCELLED'}
            elif failed:
                names = ", ".join(f"{o.name} ({err})" for o, err in failed)
                self.report({'WARNING'}, f"Baked {len(succeeded)} zone(s), but failed for: {names}")
                return {'FINISHED'}

            self.report({'INFO'}, f"Successfully baked all {len(succeeded)} Giggle simulation zone(s) (Frames {f_start}-{f_end}, {storage_mode})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Baking failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in bpy.data.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_bake_selected_cage(Operator):
    """Bake simulation cache for the active Giggle zone only"""
    bl_idname = "giggle.bake_selected_cage"
    bl_label = "Bake Active Zone"
    bl_description = "Bake only the active Giggle simulation cage"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None)
        mods = get_giggle_modifiers(obj)
        return bool(obj and obj.type == 'MESH' and settings and 0 <= settings.active_zone_index < len(mods))

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        settings = scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        active_mod = mods[idx]

        s_in = getattr(getattr(active_mod, "properties", None), "inputs", None)
        vg_name = getattr(s_in.Socket_2, "attribute_name", "") if (s_in and hasattr(s_in, "Socket_2")) else ""

        cage_obj = get_zone_cage_object(obj, vg_name) if vg_name else None
        target_sim = cage_obj if cage_obj else obj

        storage_mode = settings.bake_storage_mode
        disk_path = settings.bake_disk_path
        f_start = scene.frame_start if settings.bake_use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if settings.bake_use_scene_range else settings.bake_frame_end

        ok, msg = preflight_validate_bake(context, [target_sim], storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        try:
            ok_bake, err = execute_cage_bake_step(target_sim, context, storage_mode, disk_path, f_start, f_end)
            if not ok_bake:
                self.report({'ERROR'}, f"Baking zone failed: {err}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"Baked zone '{active_mod.name}' (Frames {f_start}-{f_end}, {storage_mode})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Baking zone failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in bpy.data.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_rebake_all(Operator):
    """Safely invalidate and rebuild every Giggle-managed simulation cache with transactional verification"""
    bl_idname = "giggle.rebake_all"
    bl_label = "Rebake All Giggle Zones"
    bl_description = "Safely purge and recalculate all Giggle physics simulation caches"
    bl_options = {'REGISTER'}

    confirm: BoolProperty(
        name="Confirm Rebake",
        description="Proceed with replacing existing simulation caches",
        default=True
    )

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def invoke(self, context, event):
        sim_objs = get_giggle_simulation_objects(context)
        if not sim_objs:
            self.report({'WARNING'}, "No active Giggle simulation zones found to rebake.")
            return {'CANCELLED'}

        has_existing = any(
            o.get('_giggle_baked_at_timestamp') or any(len(b.data_blocks) > 0 for m in o.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for b in m.bakes)
            for o in sim_objs
        )
        if has_existing and event is not None:
            return context.window_manager.invoke_props_dialog(self, width=420)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        sim_objs = get_giggle_simulation_objects(context)
        box = layout.box()
        box.alert = True
        box.label(text="Confirm Rebake All: Existing caches will be replaced!", icon='ERROR')

        col = box.column(align=True)
        for o in sim_objs:
            st, fr, stor, reason = get_cage_bake_status(o)
            row = col.row()
            row.label(text=o.name, icon='OUTLINER_OB_MESH')
            row.label(text=f"Status: {st}")

        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        layout.label(text=f"Configuration: Frames {f_start}–{f_end} | Storage: {storage_mode}")
        layout.label(text="Click OK to create a safety backup and rebake all zones.")

    def execute(self, context):
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        disk_path = getattr(settings, 'bake_disk_path', '//giggle_cache/') if settings else '//giggle_cache/'
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        sim_objs = get_giggle_simulation_objects(context)
        ok, msg = preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        backup_file = create_project_backup()
        if backup_file:
            print(f"[Giggle Backup] Project backup created at: {backup_file}")

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        succeeded = []
        failed = []

        try:
            for o in sim_objs:
                ok_bake, err = execute_cage_bake_step(o, context, storage_mode, disk_path, f_start, f_end)
                if ok_bake:
                    succeeded.append(o)
                else:
                    failed.append((o, err))

            if failed and not succeeded:
                self.report({'ERROR'}, f"Rebake failed for all {len(sim_objs)} zone(s).")
                return {'CANCELLED'}
            elif failed:
                names = ", ".join(f"{o.name} ({err})" for o, err in failed)
                self.report({'WARNING'}, f"Rebaked {len(succeeded)} zone(s), but failed for: {names}")
                return {'FINISHED'}

            self.report({'INFO'}, f"Successfully rebaked all {len(succeeded)} Giggle simulation zone(s) (Frames {f_start}-{f_end}, {storage_mode})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Rebake All failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in bpy.data.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_rebake_sim(Operator):
    """Safely invalidate and rebake all Giggle simulation zones (alias for giggle.rebake_all)"""
    bl_idname = "giggle.rebake_sim"
    bl_label = "Rebake All Zones"
    bl_description = "Safely purge existing simulation caches and rebake with current physics settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return bpy.ops.giggle.rebake_all()


class GIGGLE_OT_bake_missing(Operator):
    """Bake only unbaked or outdated simulation caches, skipping valid ones"""
    bl_idname = "giggle.bake_missing"
    bl_label = "Bake Missing / Outdated"
    bl_description = "Recalculate simulation caches only for unbaked or outdated Giggle zones"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def execute(self, context):
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        disk_path = getattr(settings, 'bake_disk_path', '//giggle_cache/') if settings else '//giggle_cache/'
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        sim_objs = get_giggle_simulation_objects(context)
        ok, msg = preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        # Filter to only missing or outdated cages
        targets = []
        for o in sim_objs:
            st, reason = check_cage_validity(o, context)
            if st != 'BAKED':
                targets.append(o)

        if not targets:
            self.report({'INFO'}, "All Giggle simulation caches are already baked and up to date.")
            return {'FINISHED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        succeeded = []
        failed = []

        try:
            for o in targets:
                ok_bake, err = execute_cage_bake_step(o, context, storage_mode, disk_path, f_start, f_end)
                if ok_bake:
                    succeeded.append(o)
                else:
                    failed.append((o, err))

            if failed and not succeeded:
                self.report({'ERROR'}, f"Bake failed for all {len(targets)} missing zone(s).")
                return {'CANCELLED'}
            elif failed:
                names = ", ".join(f"{o.name} ({err})" for o, err in failed)
                self.report({'WARNING'}, f"Baked {len(succeeded)} missing zone(s), but failed for: {names}")
                return {'FINISHED'}

            self.report({'INFO'}, f"Successfully baked {len(succeeded)} missing/outdated Giggle zone(s) (Frames {f_start}-{f_end})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Bake Missing failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in bpy.data.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_check_cache_validity(Operator):
    """Verify whether simulation caches match current animation keyframes, rig transforms, and physics settings"""
    bl_idname = "giggle.check_cache_validity"
    bl_label = "Check Cache Validity"
    bl_description = "Recalculate dependency fingerprints to verify whether simulation caches match the current scene"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def execute(self, context):
        sim_objs = get_giggle_simulation_objects(context)
        valid_cages = []
        outdated_cages = []
        unbaked_cages = []

        for o in sim_objs:
            st, reason = check_cage_validity(o, context)
            if st == 'BAKED':
                valid_cages.append(o)
            elif st == 'OUTDATED':
                outdated_cages.append((o, reason))
            else:
                unbaked_cages.append((o, reason))

        if outdated_cages:
            details = ", ".join(f"{o.name} ({r})" for o, r in outdated_cages)
            self.report({'WARNING'}, f"{len(outdated_cages)} cage(s) OUTDATED: {details}")
        elif unbaked_cages:
            self.report({'INFO'}, f"{len(valid_cages)} cage(s) match setup, {len(unbaked_cages)} unbaked.")
        else:
            self.report({'INFO'}, f"All {len(valid_cages)} Giggle simulation cache(s) match scene dependencies.")
        return {'FINISHED'}


class GIGGLE_OT_mark_cache_outdated(Operator):
    """Manually mark Giggle simulation caches as outdated"""
    bl_idname = "giggle.mark_cache_outdated"
    bl_label = "Mark Cache Outdated"
    bl_description = "Manually mark Giggle simulation caches as outdated to force recalculation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sim_objs = get_giggle_simulation_objects(context)
        for o in sim_objs:
            o['_giggle_status'] = 'OUTDATED'
            o['_giggle_last_known_valid'] = False
            o['_giggle_outdated_reason'] = "Manually marked outdated by user"
            o.update_tag(refresh={'DATA'})
        self.report({'INFO'}, f"Marked {len(sim_objs)} Giggle simulation cache(s) as outdated.")
        return {'FINISHED'}


class GIGGLE_OT_clear_sim_cache(Operator):
    bl_idname = "giggle.clear_sim_cache"
    bl_label = "Clear Giggle Cache"
    bl_description = "Purge Geometry Nodes simulation caches strictly on Giggle-managed simulation cages"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        failed_objs = []
        sim_objs = get_giggle_simulation_objects(context)
        if not sim_objs:
            self.report({'INFO'}, "No active Giggle simulation caches found to clear.")
            return {'FINISHED'}

        for obj in sim_objs:
            try:
                with context.temp_override(active_object=obj, selected_objects=[obj]):
                    del_res = bpy.ops.object.simulation_nodes_cache_delete(selected=True)
                if del_res == {'FINISHED'}:
                    obj.pop('_giggle_baked_at_timestamp', None)
                    obj.pop('_giggle_bake_fingerprint_json', None)
                    obj.pop('_giggle_bake_schema_version', None)
                    obj.pop('_giggle_baked_frame_range', None)
                    obj.pop('_giggle_baked_storage', None)
                    obj.pop('_giggle_settings_modified_at', None)
                    obj['_giggle_status'] = 'NOT_BAKED'
                    obj['_giggle_last_known_valid'] = False
                    obj['_giggle_outdated_reason'] = "Cache cleared"
                    obj.update_tag(refresh={'DATA'})
                    count += 1
                else:
                    failed_objs.append(obj.name)
            except Exception:
                failed_objs.append(obj.name)

        active = context.active_object
        if active and active not in sim_objs:
            active.pop('_giggle_baked_at_timestamp', None)
            active.pop('_giggle_bake_fingerprint_json', None)
            active.pop('_giggle_bake_schema_version', None)
            active.pop('_giggle_baked_frame_range', None)
            active.pop('_giggle_baked_storage', None)
            active.pop('_giggle_settings_modified_at', None)

        context.scene.frame_set(context.scene.frame_current)

        if failed_objs and count == 0:
            self.report({'ERROR'}, f"Failed to clear simulation cache on: {', '.join(failed_objs)}")
            return {'CANCELLED'}
        elif failed_objs:
            self.report({'WARNING'}, f"Purged cache on {count} object(s), but failed for: {', '.join(failed_objs)}")
            return {'FINISHED'}

        self.report({'INFO'}, f"Purged Giggle simulation cache on {count} object(s). Unrelated simulations preserved.")
        return {'FINISHED'}


'''

text = text[:idx_start] + new_baking_block + text[idx_end:]
print("3. Replaced baking helpers, validity checker, and operators block.")

# 4. Update VIEW3D_PT_giggle_playback
old_playback_panel = """class VIEW3D_PT_giggle_playback(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_playback"
    bl_label = "Simulation & Playback"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        obj = context.active_object

        # --- SIMULATION CACHE MANAGER CARD ---
        box_cache = layout.box()
        box_cache.label(text="Simulation Cache & Baking:", icon='FILE_CACHE')

        # Check cache status across active zones
        sim_objs = get_giggle_simulation_objects(context, obj)
        is_any_baked = False
        is_outdated = False
        bake_details = []

        for so in sim_objs:
            status, frange, storage = get_cage_bake_status(so)
            if status == 'BAKED':
                is_any_baked = True
                bake_details.append(f"{so.name}: {frange[0]}-{frange[1]} ({storage})")
            elif status == 'OUTDATED':
                is_outdated = True
                bake_details.append(f"{so.name}: OUTDATED")

        if is_outdated:
            st_box = box_cache.box()
            st_box.alert = True
            st_box.label(text="Cache Outdated (Settings changed)", icon='ERROR')
            st_box.operator("giggle.rebake_sim", text="Rebake All Zones", icon='FILE_REFRESH')
        elif is_any_baked:
            st_box = box_cache.box()
            row_st = st_box.row()
            row_st.label(text="Status: BAKED (Instant Playback)", icon='CHECKMARK')
            for bd in bake_details:
                st_box.label(text=str(bd), icon='DOT')
        else:
            st_box = box_cache.box()
            st_box.label(text="Status: REAL-TIME (Unbaked)", icon='TIME')
            st_box.label(text="Bake to scrub instantly and render safely.", icon='INFO')

        # Storage options
        if settings:
            row_store = box_cache.row(align=True)
            row_store.prop(settings, "bake_storage_mode", expand=True)

            row_range = box_cache.row(align=True)
            row_range.prop(settings, "bake_use_scene_range", text="Use Scene Range")
            if not settings.bake_use_scene_range:
                row_f = box_cache.row(align=True)
                row_f.prop(settings, "bake_frame_start", text="Start")
                row_f.prop(settings, "bake_frame_end", text="End")

        # Bake Action Buttons
        row_bake = box_cache.row(align=True)
        row_bake.scale_y = 1.2
        row_bake.operator("giggle.bake_all_cages", text="Bake All Zones", icon='PHYSICS')
        row_bake.operator("giggle.bake_selected_cage", text="Bake Active", icon='RESTRICT_SELECT_OFF')

        row_clear = box_cache.row(align=True)
        row_clear.operator("giggle.rebake_sim", text="Rebake All", icon='FILE_REFRESH')
        row_clear.operator("giggle.clear_sim_cache", text="Clear Cache", icon='TRASH')"""

new_playback_panel = """class VIEW3D_PT_giggle_playback(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_playback"
    bl_label = "Simulation & Playback"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        obj = context.active_object

        # --- SIMULATION CACHE MANAGER CARD ---
        box_cache = layout.box()
        box_cache.label(text="Simulation Cache & Baking:", icon='FILE_CACHE')

        # Check cache status across active zones
        sim_objs = get_giggle_simulation_objects(context, obj)
        all_baked = bool(sim_objs)
        any_outdated = False
        any_failed = False
        zone_statuses = []

        for so in sim_objs:
            status, frange, storage, reason = get_cage_bake_status(so)
            zone_statuses.append((so, status, frange, storage, reason))
            if status != 'BAKED':
                all_baked = False
            if status == 'OUTDATED':
                any_outdated = True
            elif status == 'FAILED':
                any_failed = True

        st_box = box_cache.box()
        if any_failed:
            st_box.alert = True
            st_box.label(text="Cache Generation Failed on one or more zones", icon='CANCEL')
        elif any_outdated:
            st_box.alert = True
            st_box.label(text="Cache Outdated (Dependencies or settings changed)", icon='ERROR')
        elif all_baked:
            st_box.label(text="Status: BAKED (All Zones Synchronized)", icon='CHECKMARK')
        else:
            st_box.label(text="Status: UNBAKED / REAL-TIME", icon='TIME')
            st_box.label(text="Bake simulations to scrub instantly and render safely.", icon='INFO')

        # Per-zone detailed status display
        if sim_objs:
            col_zones = st_box.column(align=True)
            for so, status, frange, storage, reason in zone_statuses:
                row_z = col_zones.row(align=True)
                if status == 'BAKED':
                    row_z.label(text=f"{so.name}: BAKED ({frange[0]}-{frange[1]}, {storage})", icon='CHECKMARK')
                elif status == 'OUTDATED':
                    row_z.label(text=f"{so.name}: OUTDATED ({reason})", icon='ERROR')
                elif status == 'FAILED':
                    row_z.label(text=f"{so.name}: FAILED ({reason})", icon='CANCEL')
                else:
                    row_z.label(text=f"{so.name}: NOT BAKED", icon='TIME')

        # Storage options
        if settings:
            row_store = box_cache.row(align=True)
            row_store.prop(settings, "bake_storage_mode", expand=True)

            row_range = box_cache.row(align=True)
            row_range.prop(settings, "bake_use_scene_range", text="Use Scene Range")
            if not settings.bake_use_scene_range:
                row_f = box_cache.row(align=True)
                row_f.prop(settings, "bake_frame_start", text="Start")
                row_f.prop(settings, "bake_frame_end", text="End")

        # Action Buttons
        row_bake = box_cache.row(align=True)
        row_bake.scale_y = 1.2
        row_bake.operator("giggle.bake_missing", text="Bake Missing / Outdated", icon='PLAY')
        row_bake.operator("giggle.rebake_all", text="Rebake All", icon='FILE_REFRESH')

        row_ops2 = box_cache.row(align=True)
        row_ops2.operator("giggle.check_cache_validity", text="Check Validity", icon='CHECKMARK')
        row_ops2.operator("giggle.clear_sim_cache", text="Clear Cache", icon='TRASH')

        row_act = box_cache.row(align=True)
        row_act.operator("giggle.bake_selected_cage", text="Bake Active Zone Only", icon='RESTRICT_SELECT_OFF')

        if settings:
            box_cache.prop(settings, "check_cache_on_render", text="Pre-Flight Render Check")"""

assert old_playback_panel in text, "Could not find VIEW3D_PT_giggle_playback panel"
text = text.replace(old_playback_panel, new_playback_panel, 1)
print("4. Replaced VIEW3D_PT_giggle_playback panel.")

# 5. Add render_pre handler
render_handler_code = """
@bpy.app.handlers.persistent
def render_pre_cache_check(scene):
    try:
        settings = getattr(scene, 'giggle_settings', None)
        if not settings or not getattr(settings, 'check_cache_on_render', True):
            return
        outdated = []
        unbaked = []
        for o in bpy.data.objects:
            if o.type == 'MESH' and (o.get('_giggle_cage') or (o.users_collection and any(c.name == 'Giggle_Cages' for c in o.users_collection))):
                st, reason = check_cage_validity(o, bpy.context)
                if st == 'OUTDATED':
                    outdated.append(f"{o.name} ({reason})")
                elif st != 'BAKED':
                    unbaked.append(o.name)
        if outdated or unbaked:
            print("\\n[GIGGLE PRE-FLIGHT RENDER WARNING]")
            if outdated:
                print(f"  WARNING: Rendering with OUTDATED cache on: {', '.join(outdated)}")
            if unbaked:
                print(f"  WARNING: Rendering with UNBAKED cache on: {', '.join(unbaked)}")
            print("  Recommendation: Recalculate simulation caches with 'Rebake All' before rendering.\\n")
    except Exception:
        pass
"""

# Insert render_pre_cache_check before classes definition
classes_idx = text.find("classes = (")
assert classes_idx != -1, "Could not find classes = ("
text = text[:classes_idx] + render_handler_code + "\n" + text[classes_idx:]
print("5. Added render_pre_cache_check handler function.")

# 6. Add operators to classes tuple
old_classes = """    GIGGLE_OT_bake_all_cages,
    GIGGLE_OT_bake_selected_cage,
    GIGGLE_OT_rebake_sim,"""

new_classes = """    GIGGLE_OT_bake_all_cages,
    GIGGLE_OT_bake_selected_cage,
    GIGGLE_OT_rebake_all,
    GIGGLE_OT_rebake_sim,
    GIGGLE_OT_bake_missing,
    GIGGLE_OT_check_cache_validity,
    GIGGLE_OT_mark_cache_outdated,"""

assert old_classes in text, "Could not find classes entries"
text = text.replace(old_classes, new_classes, 1)
print("6. Updated classes tuple.")

# 7. Add render_pre_cache_check to register() and unregister()
old_reg = "def register():\n    for cls in classes:\n        bpy.utils.register_class(cls)"
new_reg = """def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if render_pre_cache_check not in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.append(render_pre_cache_check)"""

assert old_reg in text, "Could not find register() insertion point"
text = text.replace(old_reg, new_reg, 1)

old_unreg = "def unregister():"
new_unreg = """def unregister():
    if render_pre_cache_check in bpy.app.handlers.render_pre:
        try:
            bpy.app.handlers.render_pre.remove(render_pre_cache_check)
        except Exception:
            pass"""
assert old_unreg in text, "Could not find unregister() insertion point"
text = text.replace(old_unreg, new_unreg, 1)
print("7. Updated register() and unregister() for render_pre handler.")

with open(INIT_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

print("\nSUCCESS: All patches written to giggle_addon/__init__.py")
