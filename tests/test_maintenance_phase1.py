"""Regression tests for maintenance phase 1 (findings 1, 2, 3, 6, 20).

Run headless against the POC scene:

    blender -b poc_cage_xpbd_kasumi.blend --python tests/test_maintenance_phase1.py \
        --python-exit-code 1

Covers:
  1  frame-range / storage / schema invalidation
  2  a failed bake keeps the previous cache
  3  backups are pruned and not duplicated when the file did not change
  6  foreign objects that only look like cages are not claimed
 20  discovery is limited to the active scene
"""

import os
import sys
import tempfile

import bpy

# Load the source under test explicitly, so an installed copy of the add-on cannot answer.
SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SOURCE_ROOT not in sys.path:
    sys.path.insert(0, SOURCE_ROOT)

import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "jiggle_under_test", os.path.join(SOURCE_ROOT, "jiggle_zone", "__init__.py"))
g = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(g)


FAILURES = []
CHECKS = 0


def check(name, condition, detail=""):
    global CHECKS
    CHECKS += 1
    if condition:
        print("PASS", name)
    else:
        print("FAIL", name, detail)
        FAILURES.append(name)


def get_cage():
    ctx = bpy.context
    cages = g.get_jiggle_simulation_objects(ctx)
    assert cages, "no Jiggle cage in the test scene"
    cage = cages[0]
    mod = next(m for m in cage.modifiers
               if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1')
    return cage, mod


def block_count(mod):
    return sum(len(b.data_blocks) for b in mod.bakes)


class _FakeBake:
    def __init__(self, blocks):
        self.data_blocks = list(range(blocks))


class _FakeMod:
    """Stand-in for a Wiggy modifier, so cache paths can be tested without a real scene."""

    def __init__(self, name, bake_target='DISK', directory='', blocks=0):
        self.type = 'NODES'
        self.node_group = type('_Group', (), {'name': name})()
        self.bake_target = bake_target
        self.bake_directory = directory
        self.bakes = [_FakeBake(blocks)]


class _FakeCage:
    def __init__(self, modifiers):
        self.modifiers = modifiers
        self.keys = {}

    def get(self, key, default=None):
        return self.keys.get(key, default)

    def __setitem__(self, key, value):
        self.keys[key] = value

    def pop(self, key, default=None):
        return self.keys.pop(key, default)


def live_addon_module():
    """The enabled add-on's module, which is what the operators actually call into.

    `preferences.addons[key].module` is the dotted name, not the module object, so the loaded
    module has to be looked up in `sys.modules`.
    """
    for key in ("bl_ext.user_default.jiggle_zone", "jiggle_zone", "jiggle_zone"):
        if bpy.context.preferences.addons.get(key) is None:
            continue
        module = sys.modules.get(key)
        if module is not None:
            return module
    return None


def test_validity_invalidation():
    ctx = bpy.context
    scene = ctx.scene
    settings = scene.jiggle_settings
    cage, mod = get_cage()

    scene.frame_start = 1
    scene.frame_end = 10
    settings.bake_use_scene_range = True
    settings.bake_storage_mode = 'PACKED'

    ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//jiggle_cache/', 1, 10)
    check("bake 1-10 succeeds", ok, err)
    status, reason = g.check_cage_validity(cage, ctx)
    check("fresh bake reads BAKED", status == 'BAKED', f"{status}: {reason}")

    scene.frame_end = 20
    status, reason = g.check_cage_validity(cage, ctx)
    check("longer scene range reads OUTDATED", status == 'OUTDATED', f"{status}: {reason}")
    check("range reason names both ranges", "1-10" in reason and "1-20" in reason, reason)

    scene.frame_end = 10
    status, reason = g.check_cage_validity(cage, ctx)
    check("range back to baked value reads BAKED", status == 'BAKED', f"{status}: {reason}")

    settings.bake_use_scene_range = False
    settings.bake_frame_start = 1
    settings.bake_frame_end = 12
    status, reason = g.check_cage_validity(cage, ctx)
    check("settings range change reads OUTDATED", status == 'OUTDATED', f"{status}: {reason}")
    settings.bake_use_scene_range = True

    settings.bake_storage_mode = 'DISK'
    status, reason = g.check_cage_validity(cage, ctx)
    check("storage change reads OUTDATED", status == 'OUTDATED', f"{status}: {reason}")
    check("modifier was not switched behind our back", mod.bake_target == 'PACKED', mod.bake_target)

    settings.bake_storage_mode = 'PACKED'
    status, reason = g.check_cage_validity(cage, ctx)
    check("storage restored reads BAKED", status == 'BAKED', f"{status}: {reason}")

    cage['_jiggle_bake_schema_version'] = '1.2.0'
    status, reason = g.check_cage_validity(cage, ctx)
    check("old fingerprint schema reads OUTDATED", status == 'OUTDATED' and 'schema' in reason.lower(),
          f"{status}: {reason}")
    cage['_jiggle_bake_schema_version'] = g.FINGERPRINT_SCHEMA
    status, reason = g.check_cage_validity(cage, ctx)
    check("current schema reads BAKED again", status == 'BAKED', f"{status}: {reason}")


def test_failed_bake_keeps_cache():
    ctx = bpy.context
    cage, mod = get_cage()
    before_blocks = block_count(mod)
    before_stamp = cage.get('_jiggle_baked_at_timestamp')
    before_status = cage.get('_jiggle_status')
    group_name = mod.node_group.name

    mod.node_group.name = 'Wiggy_not_ours'
    ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//jiggle_cache/', 1, 10)
    mod.node_group.name = group_name

    check("bake on a broken modifier fails", ok is False, err)
    check("failed bake keeps the old blocks", block_count(mod) == before_blocks,
          f"{before_blocks} -> {block_count(mod)}")
    check("failed bake keeps the old stamp", cage.get('_jiggle_baked_at_timestamp') == before_stamp)
    check("failed bake keeps the old status", cage.get('_jiggle_status') == before_status,
          f"{before_status} -> {cage.get('_jiggle_status')}")
    check("failed bake records the error", bool(cage.get('_jiggle_last_bake_error')))

    status, reason = g.check_cage_validity(cage, ctx)
    check("cache still valid after the failure", status == 'BAKED', f"{status}: {reason}")


def test_bake_operator_failure_keeps_cache():
    """A failure from the real bake call, not from the validation before it.

    The existing test renames the node group, which returns before Blender is ever asked to
    bake. This one substitutes the bake call itself, which is the path a disk error or a
    cancellation actually takes.
    """
    ctx = bpy.context
    cage, mod = get_cage()
    before_blocks = block_count(mod)
    before_stamp = cage.get('_jiggle_baked_at_timestamp')
    before_status = cage.get('_jiggle_status')
    before_fp = cage.get('_jiggle_bake_fingerprint_json')
    original = g.run_bake_operator

    try:
        g.run_bake_operator = lambda context, cage_obj: {'CANCELLED'}
        ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//jiggle_cache/', 1, 10)
        check("a cancelled bake operator fails the step", ok is False, err)
        check("a cancelled bake keeps the old blocks", block_count(mod) == before_blocks,
              f"{before_blocks} -> {block_count(mod)}")
        check("a cancelled bake keeps the old stamp",
              cage.get('_jiggle_baked_at_timestamp') == before_stamp)
        check("a cancelled bake keeps the old fingerprint",
              cage.get('_jiggle_bake_fingerprint_json') == before_fp)
        check("a cancelled bake keeps the old status", cage.get('_jiggle_status') == before_status,
              f"{before_status} -> {cage.get('_jiggle_status')}")
        check("a cancelled bake records the operator result",
              'CANCELLED' in (cage.get('_jiggle_last_bake_error') or ''),
              cage.get('_jiggle_last_bake_error'))
        status, reason = g.check_cage_validity(cage, ctx)
        check("cache still valid after a cancelled bake", status == 'BAKED', f"{status}: {reason}")

        def raising(context, cage_obj):
            raise RuntimeError("injected bake failure")

        g.run_bake_operator = raising
        ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//jiggle_cache/', 1, 10)
        check("an exception from the bake operator fails the step", ok is False, err)
        check("a raised bake keeps the old blocks", block_count(mod) == before_blocks,
              f"{before_blocks} -> {block_count(mod)}")
        check("a raised bake keeps the old stamp",
              cage.get('_jiggle_baked_at_timestamp') == before_stamp)
        check("a raised bake keeps the old fingerprint",
              cage.get('_jiggle_bake_fingerprint_json') == before_fp)
        check("a raised bake keeps the old status", cage.get('_jiggle_status') == before_status,
              f"{before_status} -> {cage.get('_jiggle_status')}")
        check("the raised error is recorded",
              'injected bake failure' in (cage.get('_jiggle_last_bake_error') or ''),
              cage.get('_jiggle_last_bake_error'))
        status, reason = g.check_cage_validity(cage, ctx)
        check("cache still valid after a raised bake", status == 'BAKED', f"{status}: {reason}")
    finally:
        g.run_bake_operator = original
        cage.pop('_jiggle_last_bake_error', None)


def test_fingerprint_change_marks_outdated():
    """The post-bake mismatch branch must not pretend the old cache came back."""
    ctx = bpy.context
    cage, mod = get_cage()
    original = g.compute_zone_fingerprint
    calls = {'n': 0}

    def drifting(cage_obj, context, storage_mode, f_start, f_end):
        fingerprint = dict(original(cage_obj, context, storage_mode, f_start, f_end))
        calls['n'] += 1
        if calls['n'] > 1:
            fingerprint['physics'] = f"drifted-{calls['n']}"
        return fingerprint

    try:
        g.compute_zone_fingerprint = drifting
        ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//jiggle_cache/', 1, 10)
        check("a changed fingerprint fails the step", ok is False, err)
        check("the reason names the dependency change",
              'modified' in (err or '').lower(), err)
        check("the bake really ran, so this is not an early return", block_count(mod) > 0,
              block_count(mod))
        check("a changed fingerprint marks the cache OUTDATED",
              cage.get('_jiggle_status') == 'OUTDATED', cage.get('_jiggle_status'))
        check("a changed fingerprint clears the valid flag",
              cage.get('_jiggle_last_known_valid') is False,
              cage.get('_jiggle_last_known_valid'))
        check("the outdated reason is stored",
              'modified' in (cage.get('_jiggle_outdated_reason') or '').lower(),
              cage.get('_jiggle_outdated_reason'))
        check("the failure is recorded as a bake error",
              'modified' in (cage.get('_jiggle_last_bake_error') or '').lower(),
              cage.get('_jiggle_last_bake_error'))

        # No rollback is claimed anywhere: the cache that is on disk is the new one, so validity
        # has to say it cannot be trusted.
        status, reason = g.check_cage_validity(cage, ctx)
        check("the cache is not reported valid after a fingerprint change", status != 'BAKED',
              f"{status}: {reason}")
    finally:
        g.compute_zone_fingerprint = original
        ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//jiggle_cache/', 1, 10)
        check("a clean rebake restores a valid cache", ok, err)
        status, reason = g.check_cage_validity(cage, ctx)
        check("the restored cache reads BAKED", status == 'BAKED', f"{status}: {reason}")


def test_bake_operator_refuses_without_backup():
    """The operator must stop when the recovery copy cannot be made."""
    cage, mod = get_cage()
    live = live_addon_module()
    if live is None or not hasattr(live, 'prepare_cache_replacement') \
            or not hasattr(bpy.ops.jiggle, 'bake_all_cages'):
        print("SKIP backup gating: add-on is not enabled in this Blender")
        return

    before_blocks = block_count(mod)
    before_stamp = cage.get('_jiggle_baked_at_timestamp')
    original = live.prepare_cache_replacement
    try:
        live.prepare_cache_replacement = lambda targets: (False, "test: backup unavailable")
        result = None
        reported = ""
        try:
            result = bpy.ops.jiggle.bake_all_cages()
        except RuntimeError as exc:
            # Blender raises for a reported ERROR instead of returning CANCELLED.
            reported = str(exc)
        check("the bake operator stops when a backup cannot be made",
              result == {'CANCELLED'} or "backup unavailable" in reported,
              f"result={result} error={reported}")
        check("the operator reports why it stopped",
              "backup unavailable" in reported or result == {'CANCELLED'},
              f"result={result} error={reported}")
        check("a refused backup leaves the cache untouched", block_count(mod) == before_blocks,
              f"{before_blocks} -> {block_count(mod)}")
        check("a refused backup leaves the stamp untouched",
              cage.get('_jiggle_baked_at_timestamp') == before_stamp)
    finally:
        live.prepare_cache_replacement = original


def test_ownership():
    ctx = bpy.context
    scene = ctx.scene
    group = bpy.data.node_groups.get('Wiggy 0.1')
    assert group is not None, "Wiggy 0.1 node group missing"

    def mesh_with_wiggy(name, marker=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
        ob = bpy.data.objects.new(name, me)
        scene.collection.objects.link(ob)
        mod = ob.modifiers.new("Jiggle", 'NODES')
        mod.node_group = group
        for key, value in (marker or {}).items():
            ob[key] = value
        return ob

    foreign = mesh_with_wiggy("Hair_Cage")
    owned = mesh_with_wiggy("Owned_Cage", {"_jiggle_cage": True})
    legacy = mesh_with_wiggy("Legacy_Cage", {"_jiggle_source_body": "Body", "_jiggle_vg_name": "VG"})
    collection = bpy.data.collections.new("Jiggle_Cages")
    scene.collection.children.link(collection)
    in_collection = mesh_with_wiggy("Collection_Cage")
    for c in list(in_collection.users_collection):
        c.objects.unlink(in_collection)
    collection.objects.link(in_collection)

    found = g.get_jiggle_simulation_objects(ctx)
    check("a cage named *_Cage is not claimed", foreign not in found)
    check("a cage in Jiggle_Cages is not claimed", in_collection not in found)
    check("a cage with the ownership flag is found", owned in found)
    check("a legacy cage is adopted and found", legacy in found)
    check("legacy adoption writes the flag", legacy.get('_jiggle_cage') is True)

    # A clothing proxy carries the same metadata a legacy cage does, plus _jiggle_proxy, and a
    # garment binds to it through Surface Deform. Attaching clothes must never turn the proxy into
    # a simulation cage.
    proxy = mesh_with_wiggy("Proxy_Target", {
        "_jiggle_source_body": "Body",
        "_jiggle_source_verts": 1000,
        "_jiggle_vg_name": "VG",
        "_jiggle_proxy": True,
    })
    garment = bpy.data.objects.new("Garment", bpy.data.meshes.new("Garment"))
    scene.collection.objects.link(garment)
    garment.modifiers.new("Jiggle_SurfaceDeform", 'SURFACE_DEFORM').target = proxy

    found = g.get_jiggle_simulation_objects(ctx)
    check("a clothing proxy is not claimed as a cage", proxy not in found)
    check("a clothing proxy is not stamped with the cage flag", not proxy.get('_jiggle_cage'))

    # The garment itself is not a cage either, whatever it is bound to.
    check("a garment bound to a proxy is not claimed", garment not in found)

    # Builds before the proxy check stamped _jiggle_cage on proxies. The proxy marker has to win,
    # or those files keep baking their clothing proxies forever.
    stale_proxy = mesh_with_wiggy("Stale_Proxy_Target", {
        "_jiggle_source_body": "Body",
        "_jiggle_vg_name": "VG",
        "_jiggle_proxy": True,
        "_jiggle_cage": True,
    })
    stale_garment = bpy.data.objects.new("Stale_Garment", bpy.data.meshes.new("Stale_Garment"))
    scene.collection.objects.link(stale_garment)
    stale_garment.modifiers.new("Jiggle_SurfaceDeform", 'SURFACE_DEFORM').target = stale_proxy

    found = g.get_jiggle_simulation_objects(ctx)
    check("a proxy already stamped as a cage is still rejected", stale_proxy not in found)
    check("the stale cage flag is removed from the proxy", not stale_proxy.get('_jiggle_cage'),
          stale_proxy.get('_jiggle_cage'))

    # A pre-1.2 cage has no metadata, so the bind is the only proof. It has to be a Jiggle bind:
    # another add-on driving its own Wiggy cage through its own Surface Deform must be left alone.
    def binder(name, target, modifier_name):
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
        scene.collection.objects.link(ob)
        ob.modifiers.new(modifier_name, 'SURFACE_DEFORM').target = target
        return ob

    foreign_bound = mesh_with_wiggy("Other_Addon_Cage")
    foreign_binder = binder("Other_Addon_Body", foreign_bound, "MyAddon_SurfaceDeform")

    jiggle_bound = mesh_with_wiggy("Jiggle_Bound_Cage")
    jiggle_binder = binder("Jiggle_Bound_Body", jiggle_bound, "Jiggle_Cage_SurfaceDeform")

    found = g.get_jiggle_simulation_objects(ctx)
    check("a foreign Wiggy cage bound by another add-on is not claimed",
          foreign_bound not in found)
    check("a legacy cage bound by a Jiggle_Cage_ modifier is claimed",
          jiggle_bound in found, [o.name for o in found])

    for ob in (foreign, owned, legacy, in_collection, proxy, garment, stale_proxy, stale_garment,
               foreign_bound, foreign_binder, jiggle_bound, jiggle_binder):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(collection)


def test_scene_isolation():
    ctx = bpy.context
    scene = ctx.scene
    cage, _ = get_cage()

    other = bpy.data.scenes.new("Other_Scene")
    copy = cage.copy()
    copy['_jiggle_cage'] = True
    other.collection.objects.link(copy)

    found_here = g.get_jiggle_simulation_objects(ctx)
    check("cage from another scene is not returned", copy not in found_here)
    check("own scene cage is still returned", cage in found_here)

    ctx.window.scene = other
    try:
        found_there = g.get_jiggle_simulation_objects(ctx)
        check("other scene returns its own cage", copy in found_there)
        check("other scene does not return the first scene's cage", cage not in found_there)
    finally:
        ctx.window.scene = scene
        bpy.data.objects.remove(copy, do_unlink=True)
        bpy.data.scenes.remove(other)


def test_bake_path_has_no_pre_delete():
    import inspect

    source = inspect.getsource(g.execute_cage_bake_step)
    check("bake path never deletes the cache first",
          'simulation_nodes_cache_delete' not in source)
    check("bake path checks the block count before trusting the result",
          'has_blocks' in source)


def test_surface_deform_scope():
    ctx = bpy.context
    scene = ctx.scene
    local_target = bpy.data.objects.new("Scope_Local", bpy.data.meshes.new("Scope_Local"))
    far_target = bpy.data.objects.new("Scope_Far", bpy.data.meshes.new("Scope_Far"))
    scene.collection.objects.link(local_target)
    scene.collection.objects.link(far_target)

    binder = bpy.data.objects.new("Scope_Binder", bpy.data.meshes.new("Scope_Binder"))
    scene.collection.objects.link(binder)
    binder.modifiers.new("sd", 'SURFACE_DEFORM').target = local_target

    other = bpy.data.scenes.new("Scope_Other")
    far_binder = bpy.data.objects.new("Scope_FarBinder", bpy.data.meshes.new("Scope_FarBinder"))
    other.collection.objects.link(far_binder)
    far_binder.modifiers.new("sd", 'SURFACE_DEFORM').target = far_target

    local = g.get_surface_deform_targets(scene.objects)
    check("a bind in this scene is seen", local_target in local)
    check("a bind from another scene is not counted", far_target not in local)

    bpy.data.objects.remove(far_binder, do_unlink=True)
    bpy.data.scenes.remove(other)
    bpy.data.objects.remove(binder, do_unlink=True)
    bpy.data.objects.remove(local_target, do_unlink=True)
    bpy.data.objects.remove(far_target, do_unlink=True)


def test_clear_cache_keeps_bystander_metadata():
    ctx = bpy.context
    scene = ctx.scene

    if not hasattr(bpy.ops.jiggle, 'clear_sim_cache'):
        print("SKIP clear cache: add-on is not installed in this Blender")
        return

    bystander = bpy.data.objects.new("Bystander", bpy.data.meshes.new("Bystander"))
    scene.collection.objects.link(bystander)
    bystander['_jiggle_baked_at_timestamp'] = 123.0
    bystander['_jiggle_bake_fingerprint_json'] = '{"animation": "x"}'
    ctx.view_layer.objects.active = bystander

    bpy.ops.jiggle.clear_sim_cache()

    check("clear cache leaves an unmanaged active object alone",
          bystander.get('_jiggle_baked_at_timestamp') == 123.0 and
          bystander.get('_jiggle_bake_fingerprint_json') == '{"animation": "x"}')
    bpy.data.objects.remove(bystander, do_unlink=True)


def test_backup_policy():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tmpdir = tempfile.mkdtemp(prefix="jiggle_backup_test_")
    blend = os.path.join(tmpdir, "backup_case.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)

    first = g.create_project_backup(dirty=False)
    second = g.create_project_backup(dirty=False)
    check("backup is created", bool(first) and os.path.exists(first), first)
    check("an explicitly clean file is not copied twice", first == second, f"{first} vs {second}")

    # The default is conservative in a background session because bpy.data.is_dirty cannot be
    # trusted there, so an automatic backup must reflect the live session rather than the file.
    auto_first = g.create_project_backup()
    bpy.context.scene["jiggle_bg_marker"] = "background-edit"
    auto_second = g.create_project_backup()
    check("a background backup does not reuse the saved file", auto_first != auto_second,
          f"{auto_first} vs {auto_second}")
    bpy.ops.wm.open_mainfile(filepath=auto_second)
    check("the background backup holds the live session",
          bpy.context.scene.get("jiggle_bg_marker") == "background-edit")
    bpy.ops.wm.open_mainfile(filepath=blend)

    backup_dir = os.path.join(tmpdir, "jiggle_backup")
    for i in range(4):
        stale = os.path.join(backup_dir, f"backup_case.blend.2020010{i}_000000.bak")
        with open(stale, "w", encoding="utf-8") as handle:
            handle.write("stale")
        os.utime(stale, (1000000000 + i, 1000000000 + i))

    newest = g.create_project_backup()
    kept = [n for n in os.listdir(backup_dir) if n.endswith(".bak")]
    check("old backups are pruned", len(kept) <= g.BACKUP_KEEP, kept)
    check("newest backup is kept", os.path.basename(newest) in kept, kept)

    # Unsaved edits must be in the backup, not just a copy of the file on disk. `dirty` is passed
    # explicitly because bpy.data.is_dirty is unreliable headless: it is True for this file only
    # because the POC scene opens dirty, and it stayed False after adding and moving objects in an
    # earlier measurement. The GUI path reads the same flag from bpy.data.is_dirty.
    bpy.context.scene["jiggle_test_marker"] = "dirty-session"
    dirty_backup = g.create_project_backup(dirty=True)
    check("unsaved edits trigger a new backup", dirty_backup != newest, dirty_backup)
    check("the live file path is unchanged",
          os.path.normcase(bpy.data.filepath) == os.path.normcase(blend), bpy.data.filepath)

    second_dirty = g.create_project_backup(dirty=True)
    check("two backups in the same second get different files", second_dirty != dirty_backup,
          f"{dirty_backup} vs {second_dirty}")
    kept = [n for n in os.listdir(backup_dir) if n.endswith(".bak")]
    check("the newest dirty backup survives pruning",
          os.path.basename(second_dirty) in kept and len(kept) <= g.BACKUP_KEEP, kept)

    bpy.ops.wm.open_mainfile(filepath=second_dirty)
    check("the backup holds the unsaved session",
          bpy.context.scene.get("jiggle_test_marker") == "dirty-session")


def test_disk_cache_snapshot():
    """A .blend backup cannot restore simulation data that lives outside it."""
    tmpdir = tempfile.mkdtemp(prefix="jiggle_disk_cache_")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(tmpdir, "disk_case.blend"))

    cache = os.path.join(tmpdir, "jiggle_cache")
    other_cache = os.path.join(tmpdir, "other_cache")
    for directory, filename, payload in ((cache, "frame.bin", b"old-cache"),
                                         (other_cache, "blob.bin", b"other")):
        os.makedirs(directory)
        with open(os.path.join(directory, filename), "wb") as handle:
            handle.write(payload)

    disk = _FakeMod("Wiggy 0.1", 'DISK', cache, blocks=4)
    packed = _FakeMod("Wiggy 0.1", 'PACKED', cache, blocks=4)
    foreign = _FakeMod("Someone Elses Nodes", 'DISK', cache, blocks=4)

    check("a disk cache directory is found",
          g.cage_disk_cache_dirs(_FakeCage([disk])) == [cache],
          g.cage_disk_cache_dirs(_FakeCage([disk])))
    check("a packed cage has no external cache",
          g.cage_disk_cache_dirs(_FakeCage([packed])) == [],
          g.cage_disk_cache_dirs(_FakeCage([packed])))
    check("another add-on's node group is ignored",
          g.cage_disk_cache_dirs(_FakeCage([foreign])) == [],
          g.cage_disk_cache_dirs(_FakeCage([foreign])))
    check("the same directory is only listed once",
          len(g.cage_disk_cache_dirs(_FakeCage([disk, disk]))) == 1,
          g.cage_disk_cache_dirs(_FakeCage([disk, disk])))

    backup_root = os.path.join(tmpdir, "jiggle_backup")
    ok, message = g.snapshot_disk_cache(_FakeCage([disk]))
    check("the external cache is snapshotted", ok, message)
    snapshots = [n for n in os.listdir(backup_root) if ".cache." in n]
    check("exactly one snapshot exists", len(snapshots) == 1, snapshots)
    copied = os.path.join(backup_root, snapshots[0], "frame.bin") if snapshots else ""
    check("the snapshot holds the cache contents",
          bool(copied) and os.path.exists(copied) and open(copied, "rb").read() == b"old-cache",
          copied)

    # Age the snapshot so pruning has something to remove.
    label = snapshots[0].split(".cache.")[0] + ".cache."
    stale = os.path.join(backup_root, f"{label}20000101_000000")
    os.makedirs(stale, exist_ok=True)
    with open(os.path.join(stale, "frame.bin"), "wb") as handle:
        handle.write(b"stale")
    os.utime(stale, (1000000000, 1000000000))

    ok, message = g.snapshot_disk_cache(_FakeCage([disk]))
    kept = [n for n in os.listdir(backup_root) if ".cache." in n]
    check("a second snapshot succeeds", ok, message)
    check("old cache snapshots are pruned", len(kept) == g.CACHE_BACKUP_KEEP, kept)
    check("the stale snapshot is the one removed", stale not in
          [os.path.join(backup_root, n) for n in kept], kept)

    original_copytree = g.shutil.copytree

    def failing_copytree(*args, **kwargs):
        raise OSError("injected copy failure")

    try:
        g.shutil.copytree = failing_copytree
        ok, message = g.snapshot_disk_cache(_FakeCage([disk]))
        check("a failed copy is reported, not raised", ok is False, f"{ok} {message}")
        check("the copy failure is explained", "injected copy failure" in message, message)
    finally:
        g.shutil.copytree = original_copytree

    # Nothing exists for a cage whose directory has never been written.
    missing = _FakeMod("Wiggy 0.1", 'DISK', os.path.join(tmpdir, "never_baked"), blocks=0)
    ok, message = g.snapshot_disk_cache(_FakeCage([missing]))
    check("a cage with no disk cache needs no snapshot", ok and message == "", f"{ok} {message}")


def test_snapshots_with_the_same_basename():
    """Two caches both called `jiggle_cache` must not prune each other."""
    tmpdir = tempfile.mkdtemp(prefix="jiggle_same_name_")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(tmpdir, "same_name.blend"))

    first = os.path.join(tmpdir, "character_a", "jiggle_cache")
    second = os.path.join(tmpdir, "character_b", "jiggle_cache")
    for directory, payload in ((first, b"character-a"), (second, b"character-b")):
        os.makedirs(directory)
        with open(os.path.join(directory, "frame.bin"), "wb") as handle:
            handle.write(payload)

    cage = _FakeCage([_FakeMod("Wiggy 0.1", 'DISK', first, blocks=2),
                      _FakeMod("Wiggy 0.1", 'DISK', second, blocks=2)])

    ok, message = g.snapshot_disk_cache(cage)
    check("both cache directories are snapshotted", ok, message)

    backup_root = os.path.join(tmpdir, "jiggle_backup")
    snapshots = [n for n in os.listdir(backup_root) if ".cache." in n]
    check("one snapshot per directory is kept", len(snapshots) == 2, snapshots)

    payloads = set()
    for name in snapshots:
        path = os.path.join(backup_root, name, "frame.bin")
        if os.path.exists(path):
            payloads.add(open(path, "rb").read())
    check("each snapshot keeps its own cache contents",
          payloads == {b"character-a", b"character-b"}, payloads)

    # A second pass must still leave both, not prune one in favour of the other.
    ok, message = g.snapshot_disk_cache(cage)
    snapshots = [n for n in os.listdir(backup_root) if ".cache." in n]
    check("a second pass keeps both directories", ok and len(snapshots) == 2, snapshots)


def test_prepare_cache_replacement():
    tmpdir = tempfile.mkdtemp(prefix="jiggle_replace_")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(tmpdir, "replace_case.blend"))

    cache = os.path.join(tmpdir, "jiggle_cache")
    os.makedirs(cache)
    marker = os.path.join(cache, "keep.bin")
    with open(marker, "wb") as handle:
        handle.write(b"keep-me")

    cached = _FakeCage([_FakeMod("Wiggy 0.1", 'DISK', cache, blocks=3)])
    uncached = _FakeCage([_FakeMod("Wiggy 0.1", 'DISK', cache, blocks=0)])

    ok, message = g.prepare_cache_replacement([uncached])
    check("nothing is required when no cache would be replaced", ok and message == "",
          f"{ok} {message}")

    original_backup = g.create_project_backup
    try:
        g.create_project_backup = lambda *args, **kwargs: None
        ok, message = g.prepare_cache_replacement([cached])
        check("a missing project backup refuses the replacement", ok is False, f"{ok} {message}")
        check("the refusal explains itself", "backup" in message.lower(), message)
        check("the existing cache is untouched after a refusal",
              open(marker, "rb").read() == b"keep-me")
    finally:
        g.create_project_backup = original_backup

    original_snapshot = g.snapshot_disk_cache
    try:
        g.snapshot_disk_cache = lambda cage_obj, keep=None: (False, "injected snapshot failure")
        try:
            ok, message = g.prepare_cache_replacement([cached])
        finally:
            g.snapshot_disk_cache = original_snapshot
        check("a missing external snapshot refuses the replacement", ok is False,
              f"{ok} {message}")
        check("the snapshot refusal explains itself",
              "injected snapshot failure" in message, message)
    finally:
        g.snapshot_disk_cache = original_snapshot

    ok, message = g.prepare_cache_replacement([cached])
    check("a saved file with a writable cache passes", ok, message)
    backup_root = os.path.join(tmpdir, "jiggle_backup")
    baks = [n for n in os.listdir(backup_root) if n.endswith(".bak")] if os.path.isdir(backup_root) else []
    snaps = [n for n in os.listdir(backup_root) if ".cache." in n] if os.path.isdir(backup_root) else []
    check("the .blend is backed up before the replacement", bool(baks), baks)
    check("the external cache is backed up before the replacement", bool(snaps), snaps)


def main():
    print("BLENDER", bpy.app.version_string, "FILE", bpy.data.filepath)
    if bpy.data.filepath.endswith("poc_cage_xpbd_kasumi.blend"):
        test_validity_invalidation()
        test_failed_bake_keeps_cache()
        test_bake_operator_failure_keeps_cache()
        test_fingerprint_change_marks_outdated()
        test_bake_operator_refuses_without_backup()
        test_bake_path_has_no_pre_delete()
        test_ownership()
        test_scene_isolation()
        test_surface_deform_scope()
        test_clear_cache_keeps_bystander_metadata()
    else:
        print("SKIP scene tests: open poc_cage_xpbd_kasumi.blend to run them")
    test_backup_policy()
    test_disk_cache_snapshot()
    test_snapshots_with_the_same_basename()
    test_prepare_cache_replacement()

    print(f"RESULT {CHECKS - len(FAILURES)}/{CHECKS} checks passed")
    if FAILURES:
        print("FAILED:", ", ".join(FAILURES))
        sys.exit(1)


main()
