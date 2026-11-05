import bpy
import sys
import os
import traceback

print("=== STARTING MILESTONE 3 ACCEPTANCE TEST SUITE ===")

try:
    # 1. Verify addon registration
    try:
        import giggle_addon
    except ImportError:
        import bl_ext.user_default.giggle_physics as giggle_addon

    version = getattr(giggle_addon, 'bl_info', {}).get('version', (2, 0, 0))
    print(f"Addon version: {version}")

    # 2. Verify all operator IDs exist in bpy.ops.giggle
    expected_ops = [
        "bake_all_cages",
        "bake_selected_cage",
        "rebake_all",
        "rebake_sim",
        "bake_missing",
        "check_cache_validity",
        "mark_cache_outdated",
        "clear_sim_cache",
    ]

    for op_id in expected_ops:
        has_op = hasattr(bpy.ops.giggle, op_id)
        print(f"  Operator bpy.ops.giggle.{op_id}: {'EXISTS' if has_op else 'MISSING'}")
        assert has_op, f"Operator giggle.{op_id} is missing!"

    # 3. Target discovery
    context = bpy.context
    scene = context.scene
    sim_objs = giggle_addon.get_giggle_simulation_objects(context)
    print(f"\nDiscovered Giggle simulation objects: {[o.name for o in sim_objs]}")
    assert len(sim_objs) >= 1, "No simulation cages discovered!"
    cage = sim_objs[0]

    # 4. Preflight test
    ok, msg = giggle_addon.preflight_validate_bake(context, sim_objs, 'PACKED', 10, 1)
    print(f"\nPreflight invalid range test: ok={ok}, msg={msg}")
    assert not ok, "Preflight should have failed on invalid frame range!"

    # 5. Clear cache test
    print("\nTesting giggle.clear_sim_cache...")
    with context.temp_override(active_object=cage, selected_objects=[cage]):
        res_clear = bpy.ops.giggle.clear_sim_cache()
    print("Clear cache result:", res_clear)
    assert res_clear == {'FINISHED'}

    st, fr, stor, reason = giggle_addon.get_cage_bake_status(cage)
    print(f"Status after clear: {st} ({reason})")
    assert st == 'NOT_BAKED'

    # 6. Test Bake Missing (should bake because it is NOT_BAKED)
    print("\nTesting giggle.bake_missing on unbaked cage...")
    orig_active = context.view_layer.objects.active
    orig_frame = scene.frame_current

    scene.giggle_settings.bake_use_scene_range = False
    scene.giggle_settings.bake_frame_start = 1
    scene.giggle_settings.bake_frame_end = 15

    res_missing = bpy.ops.giggle.bake_missing()
    print("Bake Missing result:", res_missing)
    assert res_missing == {'FINISHED'}

    # Verify state restored
    assert scene.frame_current == orig_frame, "Scene frame was not restored!"

    # 7. Verify validity immediately after bake
    st2, fr2, stor2, reason2 = giggle_addon.get_cage_bake_status(cage)
    print(f"Status after bake_missing: {st2} ({reason2})")
    assert st2 == 'BAKED'

    # Run check_cache_validity operator
    res_valid = bpy.ops.giggle.check_cache_validity()
    print("Check cache validity result:", res_valid)
    assert res_valid == {'FINISHED'}

    # 8. Test Bake Missing when already baked (should skip and finish immediately)
    print("\nTesting giggle.bake_missing when all cages are already baked...")
    res_missing_skip = bpy.ops.giggle.bake_missing()
    print("Bake Missing (skip) result:", res_missing_skip)
    assert res_missing_skip == {'FINISHED'}

    # 9. Test Invalidation via Animation Keyframe Change
    print("\nTesting Invalidation via keyframe modification...")
    arm = giggle_addon.get_driving_armature(cage)
    act = arm.animation_data.action
    fcurves = giggle_addon.get_action_fcurves(act)
    kp = fcurves[0].keyframe_points[0]
    orig_kp_y = kp.co[1]
    kp.co[1] += 0.25 # Modify keyframe

    # Re-check validity
    val_st, val_reason = giggle_addon.check_cage_validity(cage, context)
    print(f"Validity after keyframe edit: {val_st} ({val_reason})")
    assert val_st == 'OUTDATED'
    assert "Animation" in val_reason

    # 10. Test Bake Missing on outdated cage (should rebake the outdated cage)
    print("\nTesting giggle.bake_missing on OUTDATED cage...")
    res_rebake_missing = bpy.ops.giggle.bake_missing()
    print("Bake Missing (rebake) result:", res_rebake_missing)
    assert res_rebake_missing == {'FINISHED'}

    val_st2, val_reason2 = giggle_addon.check_cage_validity(cage, context)
    print(f"Validity after rebake missing: {val_st2} ({val_reason2})")
    assert val_st2 == 'BAKED'

    # Revert keyframe and re-bake using giggle.rebake_all
    kp.co[1] = orig_kp_y
    print("\nTesting giggle.rebake_all...")
    res_rebake_all = bpy.ops.giggle.rebake_all()
    print("Rebake All result:", res_rebake_all)
    assert res_rebake_all == {'FINISHED'}

    val_st3, val_reason3 = giggle_addon.check_cage_validity(cage, context)
    print(f"Validity after rebake all: {val_st3} ({val_reason3})")
    assert val_st3 == 'BAKED'

    # 11. Test alias giggle.rebake_sim
    print("\nTesting giggle.rebake_sim (backward compatibility alias)...")
    res_rebake_sim = bpy.ops.giggle.rebake_sim()
    print("Rebake Sim result:", res_rebake_sim)
    assert res_rebake_sim == {'FINISHED'}

    # 12. Test manual invalidation: giggle.mark_cache_outdated
    print("\nTesting giggle.mark_cache_outdated...")
    res_mark = bpy.ops.giggle.mark_cache_outdated()
    print("Mark outdated result:", res_mark)
    assert res_mark == {'FINISHED'}
    st_mark, _, _, r_mark = giggle_addon.get_cage_bake_status(cage)
    print(f"Status after manual mark: {st_mark} ({r_mark})")
    assert st_mark == 'OUTDATED'

    # 13. Test Pre-flight Render Handler
    print("\nTesting render_pre_cache_check handler...")
    giggle_addon.render_pre_cache_check(scene)
    print("Render pre-flight check executed cleanly without exception.")

    print("\n=======================================================")
    print("ALL MILESTONE 3 ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")
    print("=======================================================")

except Exception as exc:
    print(f"\nTEST SUITE FAILED WITH EXCEPTION: {exc}")
    traceback.print_exc()
    sys.exit(1)
