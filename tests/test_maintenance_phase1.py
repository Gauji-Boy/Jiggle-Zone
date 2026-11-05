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
    "giggle_under_test", os.path.join(SOURCE_ROOT, "giggle_addon", "__init__.py"))
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
    cages = g.get_giggle_simulation_objects(ctx)
    assert cages, "no Giggle cage in the test scene"
    cage = cages[0]
    mod = next(m for m in cage.modifiers
               if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1')
    return cage, mod


def block_count(mod):
    return sum(len(b.data_blocks) for b in mod.bakes)


def test_validity_invalidation():
    ctx = bpy.context
    scene = ctx.scene
    settings = scene.giggle_settings
    cage, mod = get_cage()

    scene.frame_start = 1
    scene.frame_end = 10
    settings.bake_use_scene_range = True
    settings.bake_storage_mode = 'PACKED'

    ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//giggle_cache/', 1, 10)
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

    cage['_giggle_bake_schema_version'] = '1.2.0'
    status, reason = g.check_cage_validity(cage, ctx)
    check("old fingerprint schema reads OUTDATED", status == 'OUTDATED' and 'schema' in reason.lower(),
          f"{status}: {reason}")
    cage['_giggle_bake_schema_version'] = g.FINGERPRINT_SCHEMA
    status, reason = g.check_cage_validity(cage, ctx)
    check("current schema reads BAKED again", status == 'BAKED', f"{status}: {reason}")


def test_failed_bake_keeps_cache():
    ctx = bpy.context
    cage, mod = get_cage()
    before_blocks = block_count(mod)
    before_stamp = cage.get('_giggle_baked_at_timestamp')
    before_status = cage.get('_giggle_status')
    group_name = mod.node_group.name

    mod.node_group.name = 'Wiggy_not_ours'
    ok, err = g.execute_cage_bake_step(cage, ctx, 'PACKED', '//giggle_cache/', 1, 10)
    mod.node_group.name = group_name

    check("bake on a broken modifier fails", ok is False, err)
    check("failed bake keeps the old blocks", block_count(mod) == before_blocks,
          f"{before_blocks} -> {block_count(mod)}")
    check("failed bake keeps the old stamp", cage.get('_giggle_baked_at_timestamp') == before_stamp)
    check("failed bake keeps the old status", cage.get('_giggle_status') == before_status,
          f"{before_status} -> {cage.get('_giggle_status')}")
    check("failed bake records the error", bool(cage.get('_giggle_last_bake_error')))

    status, reason = g.check_cage_validity(cage, ctx)
    check("cache still valid after the failure", status == 'BAKED', f"{status}: {reason}")


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
        mod = ob.modifiers.new("Giggle", 'NODES')
        mod.node_group = group
        for key, value in (marker or {}).items():
            ob[key] = value
        return ob

    foreign = mesh_with_wiggy("Hair_Cage")
    owned = mesh_with_wiggy("Owned_Cage", {"_giggle_cage": True})
    legacy = mesh_with_wiggy("Legacy_Cage", {"_giggle_source_body": "Body", "_giggle_vg_name": "VG"})
    collection = bpy.data.collections.new("Giggle_Cages")
    scene.collection.children.link(collection)
    in_collection = mesh_with_wiggy("Collection_Cage")
    for c in list(in_collection.users_collection):
        c.objects.unlink(in_collection)
    collection.objects.link(in_collection)

    found = g.get_giggle_simulation_objects(ctx)
    check("a cage named *_Cage is not claimed", foreign not in found)
    check("a cage in Giggle_Cages is not claimed", in_collection not in found)
    check("a cage with the ownership flag is found", owned in found)
    check("a legacy cage is adopted and found", legacy in found)
    check("legacy adoption writes the flag", legacy.get('_giggle_cage') is True)

    for ob in (foreign, owned, legacy, in_collection):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(collection)


def test_scene_isolation():
    ctx = bpy.context
    scene = ctx.scene
    cage, _ = get_cage()

    other = bpy.data.scenes.new("Other_Scene")
    copy = cage.copy()
    copy['_giggle_cage'] = True
    other.collection.objects.link(copy)

    found_here = g.get_giggle_simulation_objects(ctx)
    check("cage from another scene is not returned", copy not in found_here)
    check("own scene cage is still returned", cage in found_here)

    ctx.window.scene = other
    try:
        found_there = g.get_giggle_simulation_objects(ctx)
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

    if not hasattr(bpy.ops.giggle, 'clear_sim_cache'):
        print("SKIP clear cache: add-on is not installed in this Blender")
        return

    bystander = bpy.data.objects.new("Bystander", bpy.data.meshes.new("Bystander"))
    scene.collection.objects.link(bystander)
    bystander['_giggle_baked_at_timestamp'] = 123.0
    bystander['_giggle_bake_fingerprint_json'] = '{"animation": "x"}'
    ctx.view_layer.objects.active = bystander

    bpy.ops.giggle.clear_sim_cache()

    check("clear cache leaves an unmanaged active object alone",
          bystander.get('_giggle_baked_at_timestamp') == 123.0 and
          bystander.get('_giggle_bake_fingerprint_json') == '{"animation": "x"}')
    bpy.data.objects.remove(bystander, do_unlink=True)


def test_backup_policy():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tmpdir = tempfile.mkdtemp(prefix="giggle_backup_test_")
    blend = os.path.join(tmpdir, "backup_case.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)

    first = g.create_project_backup()
    second = g.create_project_backup()
    check("backup is created", bool(first) and os.path.exists(first), first)
    check("unchanged file is not copied twice", first == second, f"{first} vs {second}")

    backup_dir = os.path.join(tmpdir, "giggle_backup")
    for i in range(4):
        stale = os.path.join(backup_dir, f"backup_case.blend.2020010{i}_000000.bak")
        with open(stale, "w", encoding="utf-8") as handle:
            handle.write("stale")
        os.utime(stale, (1000000000 + i, 1000000000 + i))

    newest = g.create_project_backup()
    kept = [n for n in os.listdir(backup_dir) if n.endswith(".bak")]
    check("old backups are pruned", len(kept) <= g.BACKUP_KEEP, kept)
    check("newest backup is kept", os.path.basename(newest) in kept, kept)

    # Unsaved edits must be in the backup, not just the copy of the file on disk.
    # bpy.data.is_dirty is never True in a background session (measured: it stays False after
    # adding objects, moving them, or writing custom properties), so the flag is passed in
    # explicitly. The GUI path reads the same flag from bpy.data.is_dirty.
    bpy.context.scene["giggle_test_marker"] = "dirty-session"
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
          bpy.context.scene.get("giggle_test_marker") == "dirty-session")


def main():
    print("BLENDER", bpy.app.version_string, "FILE", bpy.data.filepath)
    if bpy.data.filepath.endswith("poc_cage_xpbd_kasumi.blend"):
        test_validity_invalidation()
        test_failed_bake_keeps_cache()
        test_bake_path_has_no_pre_delete()
        test_ownership()
        test_scene_isolation()
        test_surface_deform_scope()
        test_clear_cache_keeps_bystander_metadata()
    else:
        print("SKIP scene tests: open poc_cage_xpbd_kasumi.blend to run them")
    test_backup_policy()

    print(f"RESULT {CHECKS - len(FAILURES)}/{CHECKS} checks passed")
    if FAILURES:
        print("FAILED:", ", ".join(FAILURES))
        sys.exit(1)


main()
