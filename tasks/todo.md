# Tasks: Giggle Physics Stabilization & Audit Remediation

- [x] 1.1 Pre-flight vertex group check in `GIGGLE_OT_add_zone` (abort if group missing on active mesh)
- [x] 1.2 Enforce `ATTRIBUTE` mode on XPBD `Socket_2` in `set_mod_socket`
- [x] 1.3 Auto-reset scene frame to `frame_start` in `GIGGLE_OT_apply_preset`
- [x] 2.1 Wrap `position_giggle_modifier` in `with context.temp_override(active_object=cloth, object=cloth):` in `GIGGLE_OT_copy_zone_to_clothing`
- [x] 2.2 Assign `settings.new_zone_vg = target_vg.name` in `GIGGLE_OT_duplicate_safe_vg`
- [x] 2.3 Split delta evenly ($0.5 \times \Delta$) for midline vertices ($\lvert x \rvert < 0.0005$) in `GIGGLE_OT_split_shapekey_lr`
- [x] 3.1 Fast vertex group copying via direct `v.groups` inspection in `GIGGLE_OT_duplicate_safe_vg`
- [x] 3.2 Loop over all Giggle modifiers in `GIGGLE_OT_auto_substeps`
- [x] 3.3 Restrict hair root bounding box calculation to selected vertices or active group in `GIGGLE_OT_pin_hair_roots`
- [x] 3.4 Cache wardrobe collection hierarchy in `VIEW3D_PT_giggle_wardrobe`
- [x] 4.1 Create test script `scratch/test_audit_remediation.py`
- [x] 4.2 Run tests headless across Blender 5.3 Beta and 5.2 LTS
- [x] 4.3 Synchronize to all 3 extension directories and repack `giggle_addon.zip`
- [x] 4.4 Document updates in `walkthrough.md`
