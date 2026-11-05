# Implementation Plan: Giggle Physics Stabilization & Audit Remediation

## Overview
This plan implements fixes for:
1. Crash & Deformation Guards: Pre-flight vertex group checks in `add_zone`, socket attribute locking, and auto timeline reset on preset apply.
2. Ponytail Audit Must-Fix: Clothing modifier placement context override, duplicate group name desync, and shape key midline blending.
3. Ponytail Audit Should-Fix: Fast vertex weight iteration, multi-zone substep synchronization, localized hair root bounding box, and wardrobe collection traversal caching.
4. Testing & Packaging: Headless test runner across Blender 5.2 LTS and 5.3 Beta, synchronization to all extension directories, and zip repacking.

## Architecture Decisions
- Pre-flight validation over fallback: Never allow an XPBD zone modifier to default to full-mesh float evaluation.
- Context managers for operator execution: Use `temp_override` on target objects.
- Timeline reset on preset application: Flush velocity vectors whenever physics parameters change.

## Task List
### Phase 1: Crash & Deformation Guards
- [ ] Task 1.1: Pre-flight Vertex Group Validation in `GIGGLE_OT_add_zone`
- [ ] Task 1.2: Enforce `ATTRIBUTE` Type on XPBD Zone Sockets (`Socket_2`)
- [ ] Task 1.3: Timeline Auto-Flush on Preset Apply (`GIGGLE_OT_apply_preset`)

### Phase 2: Ponytail Audit Must-Fix (Core Functionality)
- [ ] Task 2.1: Context Override in `GIGGLE_OT_copy_zone_to_clothing`
- [ ] Task 2.2: Name Resolution in `GIGGLE_OT_duplicate_safe_vg`
- [ ] Task 2.3: Midline Seam Blending in `GIGGLE_OT_split_shapekey_lr`

### Phase 3: Ponytail Audit Should-Fix (Performance & Ergonomics)
- [ ] Task 3.1: Fast Vertex Group Weight Iteration
- [ ] Task 3.2: Multi-Zone Substep Synchronization
- [ ] Task 3.3: Localized Bounding Box for Hair Root Pinning
- [ ] Task 3.4: Cached Wardrobe Scene Collection Traversal

### Phase 4: Multi-Version Test, Distribution & Documentation
- [ ] Task 4.1: Automated Headless Verification Suite (`scratch/test_audit_remediation.py`)
- [ ] Task 4.2: Headless Cross-Version Execution (5.2 LTS & 5.3 Beta)
- [ ] Task 4.3: Synchronize Extension Paths & Repack `giggle_addon.zip`
- [ ] Task 4.4: Update Walkthrough
