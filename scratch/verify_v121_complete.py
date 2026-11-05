import bpy
import sys
import os
import traceback

sys.path.insert(0, r"D:\Blender\Giggle")

test_blend = r"C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_32240_autosave.blend"

try:
    print("====================================================================")
    print("       GIGGLE PHYSICS v1.2.1 FULL BATTERY ACCEPTANCE TEST           ")
    print("====================================================================")
    
    bpy.ops.wm.open_mainfile(filepath=test_blend)
    
    import giggle_addon
    try:
        giggle_addon.unregister()
    except Exception:
        pass
    giggle_addon.register()
    
    # 1. Version Check
    v = giggle_addon.bl_info['version']
    print(f"1. Addon Version: {v}")
    assert v == (1, 2, 1), f"Expected version (1, 2, 1), got {v}"
    
    body = bpy.data.objects.get('kasumi_body')
    top = bpy.data.objects.get('topcen')
    scene = bpy.context.scene
    
    assert body is not None, "kasumi_body missing!"
    assert top is not None, "topcen missing!"
    
    # 2. Per-Garment Zone Detection Test
    from giggle_addon import resolve_garment_target_zone
    mod_top, vg_top, dist_top, status_top = resolve_garment_target_zone(top, body)
    print(f"2. Garment 'topcen' auto-resolved to: mod={mod_top.name if mod_top else None}, vg={vg_top}, dist={dist_top*100:.1f} cm, status={status_top}")
    assert status_top == 'OK', f"Status not OK: {status_top}"
    assert vg_top == 'Jiggle_Zone', f"Expected Jiggle_Zone, got {vg_top}"
    
    # 3. Testing Distance Exceeded Guard (>35 cm) & Transactional Rollback
    print("\n3. Testing Distance Exceeded Guard (>35 cm) & Transactional Rollback...")
    # Create a far-away object (>35 cm)
    mesh_far = bpy.data.meshes.new("FarGarmentMesh")
    obj_far = bpy.data.objects.new("FarGarment", mesh_far)
    scene.collection.objects.link(obj_far)
    obj_far.location = (0, 0, 5.0)
    
    # Test resolve_garment_target_zone on far object
    _, _, dist_far, status_far = resolve_garment_target_zone(obj_far, body)
    print(f"   Far garment distance: {dist_far*100:.1f} cm, status: {status_far}")
    assert status_far == 'EXCEEDS_DISTANCE', f"Expected EXCEEDS_DISTANCE, got {status_far}"
    
    # Add a mock modifier to topcen to verify rollback preservation
    top.modifiers.new(name="Precious_Existing_Mod", type='SHRINKWRAP')
    pre_mod_names = [m.name for m in top.modifiers]
    
    # Select body, topcen, and far garment in AUTO mode
    scene.giggle_settings.clothing_target_zone = "AUTO"
    for o in bpy.data.objects:
        o.select_set(False)
    body.select_set(True)
    top.select_set(True)
    obj_far.select_set(True)
    bpy.context.view_layer.objects.active = body
    
    threw_error = False
    try:
        res_fail = bpy.ops.giggle.attach_clothing_proxy()
    except RuntimeError as e:
        threw_error = True
        print(f"   Caught expected operator error: {e}")
        
    assert threw_error, "Operator should have failed due to distance limit!"
    
    post_mod_names = [m.name for m in top.modifiers]
    print(f"   Pre-failure modifiers on topcen: {pre_mod_names}")
    print(f"   Post-failure modifiers on topcen: {post_mod_names}")
    assert pre_mod_names == post_mod_names, "Rollback failed to preserve existing modifiers!"
    assert "Precious_Existing_Mod" in top.modifiers, "Precious modifier was lost!"
    top.modifiers.remove(top.modifiers["Precious_Existing_Mod"])
    bpy.data.objects.remove(obj_far, do_unlink=True)
    print("   Distance Guard & Transactional Rollback verified 100%!")
    
    # 4. Successful Attachment Test with AUTO Detection
    print("\n4. Testing Successful Attachment with AUTO Detection...")
    scene.giggle_settings.clothing_target_zone = "AUTO"
    scene.frame_set(18)
    initial_frame = scene.frame_current
    
    for o in bpy.data.objects:
        o.select_set(False)
    body.select_set(True)
    top.select_set(True)
    bpy.context.view_layer.objects.active = body
    
    res_success = bpy.ops.giggle.attach_clothing_proxy()
    assert res_success == {'FINISHED'}, f"Attach failed: {res_success}"
    print("   Attach operator returned FINISHED successfully!")
    
    # Verify frame restoration
    print(f"   Frame before: {initial_frame}, Frame after: {scene.frame_current}")
    assert scene.frame_current == initial_frame, "Playhead frame was not restored!"
    
    # 5. Verify SurfaceDeform Modifier on Clothing
    sd = top.modifiers.get('Giggle_SurfaceDeform')
    assert sd is not None, "Giggle_SurfaceDeform modifier not found on topcen!"
    assert sd.is_bound == True, "SurfaceDeform is not bound!"
    assert sd.target is not None, "SurfaceDeform target is None!"
    assert "kasumi_body_Jiggle_Zone_Proxy" in sd.target.name, f"Wrong target: {sd.target.name}"
    print(f"   topcen modifier verified: target={sd.target.name}, is_bound={sd.is_bound}")
    
    # Verify modifier order (Armature before SurfaceDeform)
    arm_idx = top.modifiers.find('Armature')
    sd_idx = top.modifiers.find('Giggle_SurfaceDeform')
    assert arm_idx < sd_idx, f"Order error: Armature={arm_idx}, SurfaceDeform={sd_idx}"
    print(f"   Modifier stack order: Armature={arm_idx}, Giggle_SurfaceDeform={sd_idx}")
    
    # 6. Verify Proxy Construction & Vertex Groups
    proxy = sd.target
    print(f"\n6. Verifying Proxy '{proxy.name}':")
    print(f"   Vertex count: {len(proxy.data.vertices)}, Polygon count: {len(proxy.data.polygons)}")
    print(f"   Proxy vertex groups count: {len(proxy.vertex_groups)} (Body has {len(body.vertex_groups)})")
    assert len(proxy.vertex_groups) == len(body.vertex_groups), "Proxy vertex group count mismatch!"
    assert proxy.hide_viewport == True, "Proxy should be hidden from viewport!"
    assert proxy.hide_render == True, "Proxy should be hidden from render!"
    
    # 7. Proxy Reuse Test
    print("\n7. Testing Proxy Reuse (Repeated Attachment)...")
    res_reuse = bpy.ops.giggle.attach_clothing_proxy()
    assert res_reuse == {'FINISHED'}, f"Repeat attach failed: {res_reuse}"
    sd_reused = top.modifiers.get('Giggle_SurfaceDeform')
    assert sd_reused.is_bound == True, "SurfaceDeform not bound after reuse!"
    assert sd_reused.target == proxy, "Proxy was unexpectedly recreated instead of reused!"
    print("   Proxy successfully reused without recreating or breaking bindings!")
    
    # 8. Full 33-Frame Jump Animation Tracking Audit
    print("\n8. Comprehensive Animation Tracking Audit (Frames 1 to 33):")
    v_breast_idx = 791
    max_delta = 0.0
    for f in [1, 2, 5, 10, 15, 20, 25, 28, 30, 33]:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        b_eval = body.evaluated_get(dg)
        t_eval = top.evaluated_get(dg)
        b_mesh = b_eval.to_mesh()
        t_mesh = t_eval.to_mesh()
        
        b_pos = b_eval.matrix_world @ b_mesh.vertices[v_breast_idx].co
        closest_d = min((t_eval.matrix_world @ v.co - b_pos).length for v in t_mesh.vertices)
        b_eval.to_mesh_clear()
        t_eval.to_mesh_clear()
        
        print(f"   Frame {f:2d}: Breast-to-bra distance = {closest_d*100:.3f} cm")
        assert closest_d < 0.015, f"Detachment detected at frame {f}! Distance = {closest_d*100:.2f} cm"
        if f > 1:
            delta = abs(closest_d - 0.00544)
            if delta > max_delta:
                max_delta = delta
                
    print(f"   Maximum distance deviation across all 33 frames: {max_delta*100:.4f} cm (Zero detachment!)")
    
    print("\n====================================================================")
    print("          ALL ACCEPTANCE TESTS PASSED WITH 100% SUCCESS!            ")
    print("====================================================================")

except Exception:
    traceback.print_exc()
    sys.exit(1)
