# Changelog

## Unreleased — maintenance phase 1 (reliability, no new features)

- **Cache invalidation now uses the requested settings** (`check_cage_validity`): extending the
  scene range, changing the settings range, or switching `PACKED`/`DISK` marks the cache
  `OUTDATED` instead of `BAKED`. The comparison previously read the stored values back on both
  sides, so it always matched.
- **Fingerprint schema is enforced**: a cache written with a different
  `FINGERPRINT_SCHEMA` is reported `OUTDATED` with the reason, instead of being judged with the
  current layout.
- **Rebake no longer deletes the cache first**: `execute_cage_bake_step` bakes over the existing
  cache (Blender re-bakes in place — verified against a clean bake) and only records the new
  fingerprint on success. A failed bake keeps the previous working cache and its status.
- **Backups are pruned**: `create_project_backup` keeps the newest copy only, skips the copy when
  the `.blend` has not changed since the last one, and no longer leaves one 150 MB file per click.
- **Simulation ownership is explicit**: discovery only claims cages created by Giggle (or proven
  by a Surface Deform bind / the 1.2 body link). A mesh that merely ends in `_Cage` or sits in a
  `Giggle_Cages` collection is left alone, so another Wiggy-based add-on's simulation can no
  longer be baked or cleared.
- **Operations stay in the active scene**: discovery, the render pre-flight check and the
  armature fallback no longer walk `bpy.data.objects`, so a second scene's cages are not baked
  or cleared.
- **Tests**: added `tests/test_maintenance_phase1.py` (30 checks covering the five areas above)
  and `tests/run_tests.ps1`, which runs it plus the Milestone 3 acceptance suite on Blender 5.2
  and 5.3.

## 2.0.0 — Cage-Accelerated XPBD & Simulation Cache Manager

### Milestone 1: Performance Foundation
- **Independent Per-Zone Substeps Auto-Tuning**: Auto-tuning can now tune exclusively the active zone (`all_zones=False`) without touching or slowing down other calmer zones.
- **First-Frame Simulation Cache Clear**: Introduced `giggle.clear_sim_cache` and rewound `giggle.reset_sim` to drop dirty simulation cache states and eliminate initial-frame jumps.
- **Performance Diagnostics Panel**: Added real-time 3D Viewport panel (`VIEW3D_PT_giggle_diagnostics`) alerting against high subdivision levels and GPU subdivision bugs in Blender 5.3 Beta.

### Milestone 2: Native Cage XPBD Engine
- **Dual Mode Architecture**: Full-Mesh XPBD remains 100% available as a legacy/hero option via `giggle.toggle_simulation_mode`. Existing project files are never force-converted.
- **Automatic Simulation Cage Generator (`giggle.generate_cage`)**:
  - Rest-pose isolation: Extracts geometry with Armature in `REST` pose at `frame_start`.
  - Zone boundary dilation: Expands vertex group selection by +2 edge rings for stable boundary anchoring.
  - Decimation & Manifold clean: Triangulates and decimates proxy down to ~450 vertices (96.7% fewer simulated verts).
  - Automated Rigging: Automatically sets up `Armature` -> `Wiggy 0.1` on the cage proxy.
  - Non-destructive Surface Deform: Adds `Surface Deform` with `vertex_group` influence mask to the character mesh and binds at rest pose with ACID rollback on failure.
  - Clothing Auto-Routing: Garments assigned to the zone follow the proxy cage directly.
- **Multi-Zone Scaling**: Verified 10.55x faster evaluation on dual-zone setups (Chest + Glutes) with zero zone competition.

### Milestone 3: Transactional Baking & Lazy Dependency Fingerprinting
- **Transactional Rebake All (`giggle.rebake_all`, `giggle.rebake_sim`)**: Recalculate and replace every Giggle-managed simulation cache for the character with confirmation dialog, preflight validation, automatic project safety backup, individual cage execution, and per-zone status reporting.
- **Selective Bake Missing / Outdated (`giggle.bake_missing`)**: Intelligently evaluates cage validity and recalculates only unbaked or outdated simulation caches, skipping already valid caches to maximize artist productivity.
- **Lazy Dependency Fingerprinting System**:
  - Deterministic SHA-256 cryptographic hashing across 5 independent dependency domains:
    1. *Animation*: Rig action keyframes, coordinates, Bezier handles, and interpolation modes.
    2. *Armature*: Bone rest transforms, head/tail vectors, and pose bone constraints.
    3. *Physics*: Wiggy 0.1 XPBD modifier inputs (damping, elasticity, gravity, substeps, mass).
    4. *Geometry*: Cage vertex counts, rest coordinates, and source body vertex group weights.
    5. *Simulation*: Frame ranges, scene FPS, and storage modes (`PACKED` vs `DISK`).
  - Native support for Blender 5.2 and 5.3 Layered Actions (`action.layers -> strips -> channelbags -> fcurves`) as well as legacy Action datablocks.
  - Zero Redraw Overhead: Evaluation occurs strictly on discrete events (bake completion, check validity button, pre-flight render check). Panel redraw reads cached properties in 0.001 ms without F-curve or geometry traversal.
- **On-Demand Validation (`giggle.check_cache_validity`, `giggle.mark_cache_outdated`)**: Operator to check cache validity against scene state and display human-readable invalidation reasons.
- **Pre-Flight Render Check (`render_pre_cache_check`)**: Persistent `render_pre` handler with toggle in scene settings (`settings.check_cache_on_render`) warning animators if rendering with stale or unbaked caches.
- **Strict Target Isolation**: Operates exclusively on Giggle-managed cages. Unrelated Geometry Nodes modifiers and simulations are completely protected.

## 1.2.1 — Bulletproof Transactional Clothing Attachment & Spatial Auto-Detection

### Clothing Attachment & Transactional Proxy Engine
- **Pre-Commit Dependent Garment Verification**: Rebinding of unselected dependent garments to replacement proxies is fully staged and verified (`is_bound == True`) prior to deleting old proxies. If any dependent fails, all targets and bindings are reverted and the old proxy is preserved.
- **Immediate Temporary Proxy Tracking**: Temporary proxies and their mesh datablocks are registered immediately upon creation so unexpected exceptions during mesh extraction or topology cleanup cannot orphan objects or meshes in the scene.
- **Robust Stale Proxy Detection (Fingerprinting)**: Proxies now store source body identity, source vertex count, and target vertex group metadata. Proxies are only reused when all topology and zone parameters match; modified geometry triggers a clean rebuild.
- **Geometry-Aware Surface Proximity**: Clothing target zone auto-detection now measures true surface-to-surface vertex proximity between clothing and weighted body zones, replacing crude centroid distance heuristics.
- **Character Scale Awareness**: Distance and ambiguity rejection thresholds dynamically scale with character body height, supporting characters modeled from 0.01× to 100× scales without false rejections.
- **Multi-Garment UI Preview**: The N-panel now previews per-garment zone resolutions and proximity distances when multiple clothing meshes are selected simultaneously.
- **Selective Modifier Cleanup**: Finalizing clothing attachment selectively removes only add-on managed follow modifiers and `Giggle_SurfaceDeform`, protecting unrelated user Geometry Nodes and Wiggy solvers on clothing.
- **Dedicated Hidden Proxies Collection**: Proxies are stored in an isolated, hidden `Giggle_Proxies` collection with standard display types, eliminating black wireframe cages and viewport clutter on `Alt+H`.
- **Complete Context & Mode Preservation**: Invocation mode (`OBJECT`, `POSE`, etc.) and reused proxy visibility states are captured and faithfully restored on completion or rollback.

### Jump Dynamics, XPBD Compliance Calibration & Crease Elimination (v1.2.0.1)
- **Fixed Preset Composition Bug**: Resolved root cause where generic `MOTION_PROFILES` destructively stomped individual anatomical preset dictionaries during module initialization.
- **Anatomical Safety Layer (`enforce_anatomical_safety`)**: Clamped joint-spanning zones (buttocks, upper thighs, groin) to physical bounds.
- **XPBD Compliance Calibration**: Grounded `Socket_6` ("Stretching") and `Socket_30` ("Bending") in true Geometry Nodes XPBD mathematics ($\text{Compliance} = \text{Softness}^5$).
- **Action / Jump Safety Guard (`giggle.apply_action_safety`)**: Dynamic safety guard that auto-scales solver substeps based on scene framerate and tightens travel/sway/wobble for explosive jumps.
- **Crease Elimination via Distance Falloff (`giggle.generate_distance_falloff`)**: Generates smooth spherical/ellipsoidal distance-falloff weight transitions across vertex groups to completely eliminate sharp localized vertex creasing.

## 1.2.0 — Preset and stability rework

### Presets and motion
- Reworked all 86 unique preset recipes into 17 distinct response profiles with broader differences in softness, sway, wobble, damping, travel, volume retention, stretch resistance, and bending resistance.
- Kept anatomy-specific mass and mass-by-area settings from each recipe.
- Presets now explicitly set global influence and gravity state so switching recipes does not inherit stale values from the previous preset.
- Reworded names, descriptions, and controls to avoid unsupported claims of calibrated Hz, kilogram, or biomechanical measurements.
- Added profile identity and motion-feel summaries to preset descriptions.

### Workflow fixes
- Made support-level application repeatable: choosing the same support level repeatedly no longer compounds changes.
- Manual value edits now mark the zone as Custom and invalidate the support-level baseline.
- Restricted creation of new zones to Wiggy XPBD; existing Jiggle V2 modifiers remain available for legacy scenes.
- Fixed mode/category-dependent preset selection and vertex-group auto-suggestions.
- Added validation for required vertex-group input and rollback if new-zone setup fails.
- Restore Subdivision Surface viewport state and levels after zone creation.
- Fixed shape-key splitting so the source key remains as a muted backup rather than adding its deformation a second time.
- Improved wardrobe collection cache invalidation for renames and membership changes.
- Preserve active-object and playback synchronization state during clothing deformation rebinding.

### Compatibility and packaging
- Set add-on and manifest version to 1.2.1.
- Require Blender 5.2+ to match the bundled Wiggy asset version.
