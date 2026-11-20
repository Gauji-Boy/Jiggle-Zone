# Changelog

## 3.5.0 — Wiggy 0.2.1 and Ripple Dynamics

### Added
- Bundled `Wiggy_0.2.1.blend` (1,519,926 bytes, SHA-256
  `4328183f843cd961fca0f836ac84cadb0e62dae285f97410877c07bcd82b8625`). New zones use
  `Wiggy 0.2.1`; `Wiggy 0.1`, `Wiggy 0.2.0`, the Collider and Wiggy Wind asset mappings,
  and the Back Faces implementation are unchanged.
- Three per-zone Ripple controls, off by default, mapped to the validated sockets
  `Socket_145` (Ripple 0–1, default 0), `Socket_146` (Ripple Speed 0.2–10, default 1.5) and
  `Socket_147` (Ripple Fade 0.01–1, default 0.08). A compact **Ripple Dynamics** section
  in Dynamics & Inertia shows Ripple first and disables Speed/Fade while Ripple is zero.
- Optional **Post-Simulation Smoothing** toggle mapped to the existing `Socket_98`,
  default off. It uses the solver's own smoothing and adds no extra modifier.

### Changed
- Wave and per-slot collider controls now recognise every released 0.2.x group, so
  opening a 0.2.0 project after upgrading does not hide its controls.
- Manifest and `bl_info` report 3.5.0.

### Performance and documentation notes
- Headless Ripple measurements: +6.29 ms (+39.2%) mean frame time with a 256-face collider
  and +8.51 ms (+55.1%) with an ~84k-face collider. Pre-contact Ripple-on frames cost
  about 5.81 ms / 7.95 ms more than Ripple-off, so the validator's "zero inactive overhead"
  headline is not accurate. Interactive viewport profiling has not been performed.
- The upstream Markdown validation report quotes 1,514,646 bytes for the 0.2.0 asset;
  the results JSON and the shipped file are 1,464,782 bytes with the same SHA-256.
  Geometry Nodes simulation-zone caching is confirmed; standard point caching is not.

## 3.4.0 - Collider back-face filter

### Added
- Added **Mark Back Faces** / **Clear Back Faces** for collider objects. Selected faces are
  excluded from collision through a bundled `Back Faces` Geometry Nodes modifier that writes
  the solver's own exclusion attribute, so the mesh, its vertices, vertex groups and the
  `Collider` modifier are never modified.
- Added a **Collider Back Faces** sidebar panel showing how many faces are excluded, and why a
  mask is currently disabled.

### Fixed
- A stale face mask can no longer be applied to different geometry. The collider's topology is
  recorded exactly (every corner index, every face's corner count, and the four domain sizes),
  so any change of face order or connectivity is caught even when every count stays the same.
  The check runs in depsgraph_update_pre, before the evaluation that would use the mask, and a
  mask that no longer matches is muted in the modifier stack. The reason is shown in the panel,
  and the mask is kept so restoring the original topology re-enables it.
- A mask is now fail-closed: when no usable topology record exists, when the record came from an
  older sampled format, or when the check itself fails, the filter is disabled instead of being
  applied to faces the record cannot vouch for.
- Face selection is read from the live Edit Mode BMesh, so **Mark Back Faces** uses the faces
  selected in Edit Mode and the mask is written against the mesh the modifier stack evaluates.
- Boundary colliders, objects without a `Collider` modifier, empty selections and linked
  objects are refused instead of writing a filter that could not work.

## 3.3.0 — Wiggy multi-collider support

### Added
- Added four per-zone collider object and optional vertex-group slots for Wiggy 0.2.0 while
  retaining the existing `Socket_7` collection workflow and hiding slot controls for Wiggy 0.1.
- Added selected-mesh slot assignment with warnings for duplicate processing through a slot and
  the collection input.

### Fixed
- Scene collider controls now mirror each active zone's modifier inputs without cross-zone writes
  or unnecessary bake invalidation.
- Socket writes distinguish omitted values, explicit object/collection clears, strings, and
  numeric/vector values.
- Physics fingerprints encode datablock type, full name and linked-library filepath so object and
  collection inputs remain stable across save/reopen.

## 3.2.0 — Wiggy 0.2.0 wave controls

### Added
- Added per-zone **Return Wave**, **Relax Time** and **Decay** controls for compatible Wiggy 0.2.0
  modifiers, backed by `Socket_141`, `Socket_142` and `Socket_143`.
- The controls are shown only when all three sockets are available. Wiggy 0.1 modifiers remain
  unchanged, and existing presets preserve these settings.

## 3.1.0 — Wiggy 0.2.0 for new zones

### New zones
- New zones are created on the bundled **Wiggy 0.2.0** solver, shipped as
  `assets/Wiggy_0.2.0.blend`.
- 0.2.0 adds 11 solver inputs (54 in total) and keeps every one of the 43 inputs 0.1 had: none
  were removed, renamed or retyped, and the 86 bundled presets still address the same 13 sockets.
- Presets, support profiles, colliders and the `Socket_2` vertex-group input behave the same on
  both versions.

### Existing projects
- A zone keeps the node group its file already embeds. Opening a project saved with 3.0.0 injects
  no 0.2 group or replaces its 0.1 solver; zones added to that project afterwards use 0.2.0
  alongside the 0.1 ones.
- Cage creation inherits the group from the source zone, so a 0.1 zone keeps a 0.1 cage.
- `assets/Wiggy_0.1.blend` stays in the package, so existing files keep resolving their group.

### Fixed
- Solver recognition is an explicit allow-list of the bundled groups instead of a hardcoded
  `"Wiggy 0.1"` comparison at 36 call sites. Every one of those sites failed silently when it did
  not match, so a 0.2 zone could be skipped by an operator or drawn as an empty panel.
- The asset file is chosen from an explicit group-to-file map. An unknown group now loads nothing
  instead of silently reading a Wiggy asset.

## 3.0.0 — Jiggle Zone rename (breaking identity change)

### Renamed
- The product is now **Jiggle Zone**. The extension id is `jiggle_zone`, the operator
  namespace is `jiggle.*`, and stored markers use the `_jiggle_` prefix.
- The proxies collection is `Jiggle_Proxies` and the runtime collection is
  `_tmp_Jiggle_SurfaceDeform`.
- The package folder is `jiggle_zone/` and the release artifact is `jiggle-zone.zip`.

### Upgrading from Giggle 2.x
- The extension id changed, so Blender treats this as a different add-on. Install Jiggle Zone
  **before** removing **Giggle Soft Body Physics**, open each 2.x project once, save it, then
  remove the old add-on.
- Reason: Blender discards an unregistered PropertyGroup when a file loads, so the panel
  settings (`scene.giggle_settings`: bake range, disk path, preset selection) are only copied
  while 2.1 is still enabled. The stored values are not deleted from the file and remain
  readable by 2.1.
- Markers: `_giggle_*` keys are copied to `_jiggle_*` on first load. Legacy keys are kept, so
  cage and bake links survive.
- Collection: `Giggle_Proxies` becomes `Jiggle_Proxies`. A migrated file reopened in 2.1 will
  not find the renamed collection, and proxies must be re-linked.
- Operators: `giggle.*` is removed with no alias. Keymaps and scripts must be rebound to
  `jiggle.*`.
- Round trip: a 3.0 file still resolves cage markers and old panel settings when reopened in
  2.1, but that is not a supported workflow.


### Behaviour
- No simulation behaviour changes. This is the 2.1.0 engine under a new identity.
- **Preserved clothing attachments during cage rebuilds:** Cage discovery now distinguishes
  cage-specific Surface Deform modifiers from clothing attachment modifiers, preventing legacy
  `Giggle_SurfaceDeform` and current `Jiggle_SurfaceDeform` clothing bindings from being mistaken
  for cage bindings or removed.


## 2.1.0 — Cage XPBD workflow and reliable clothing attachment

### Added
- New jiggle zones generate **Cage XPBD** automatically by default, with the existing
  Full-Mesh XPBD path retained as an explicit fallback and hero-shot option.
- Cage generation now performs rest-pose isolation, zone-boundary dilation, decimation,
  manifold sanitization, automated cage rigging, and Surface Deform binding.

### Reliability
- Failed cage binding preserves the zone and exposes explicit recovery actions: retry
  cage generation or keep the zone on Full-Mesh XPBD.
- Cage manifold sanitization removes non-manifold and loose geometry while preserving
  the expected spatial envelope and reports its diagnostics.
- Surface Deform binding and clothing attachment use transactional staging and rollback,
  including the Rest Pose workflow, so failed rebinding does not destroy a working setup.
- Clothing proxies are isolated in the hidden `Giggle_Proxies` collection and remain
  protected from cage discovery and simulation-cache operations.

### Compatibility and verification
- Verified on Blender 5.2.2 LTS and Blender 5.3.0.
- Existing Full-Mesh and Jiggle V2 projects remain supported; existing scenes are not
  force-converted to cage mode.
- This release continues to use the bundled Wiggy 0.1 asset. The Wiggy 0.2.0 port is
  intentionally separate and is not included in 2.1.0.


## 2.0.1 — maintenance phase 1 (reliability, no new features)

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
- **Backups are pruned and back up the live session**: `create_project_backup` keeps the newest
  copy only, skips the copy when the `.blend` has not changed since the last one, never reuses a
  filename within the same second, and writes the *current session* (not the stale file on disk)
  when the project has unsaved edits. A cache replacement now backs up from `bake_all`,
  `bake_selected`, `rebake_all` and `bake_missing`, not only from `rebake_all`, and only when a
  cache is actually about to be replaced. In a background session the unsaved-changes flag cannot
  be trusted, so the live session is written by default there: one extra save beats a backup that
  does not contain the work being protected.
- **Simulation ownership is explicit**: discovery only claims cages created by Giggle (or proven
  by the 1.2 body link / a Surface Deform modifier Giggle itself named, `Giggle_Cage_*`). A mesh
  that merely ends in `_Cage` or sits in a `Giggle_Cages` collection is left alone, so another
  Wiggy-based add-on's simulation can no longer be baked or cleared — including a foreign Wiggy
  cage driven through that add-on's own `Surface Deform`. A Giggle bind is accepted as
  per-session proof only; it does not stamp a permanent ownership flag on a mesh.
- **Clothing proxies are never adopted as cages**: the proxy objects created by
  `giggle.attach_clothing_proxy` carry the same `_giggle_source_body` / `_giggle_vg_name` pair a
  legacy cage does, plus a copied Wiggy modifier and a Surface Deform bind from the garment.
  `_giggle_proxy` is checked *before* `_giggle_cage`, and a stale `_giggle_cage` stamp left by an
  older build is deleted, so attaching clothes cannot turn a proxy into a bake target even in
  files written by those builds.
- **External `DISK` caches are backed up too**: a `.blend` backup cannot restore simulation data
  that lives in a cache directory, so `snapshot_disk_cache` copies each cage's `bake_directory`
  into `giggle_backup/` (pruned to the newest copy) before a bake replaces it. The snapshot label
  includes a digest of the source path, so two caches both named `giggle_cache` cannot prune each
  other's copies.
- **A bake will not replace a cache it cannot back up**: `prepare_cache_replacement` returns a
  failure when the file is unsaved or a backup cannot be written, and `bake_all_cages`,
  `bake_selected_cage`, `rebake_all` and `bake_missing` now cancel with the reason instead of
  overwriting the cache. This is a recovery point, not a transaction: if Blender overwrites the
  cache and then fails, only `giggle_backup/` has the previous data.
- **Bake-failure handling is covered by injected operator failures**: `run_bake_operator` is now a
  separate seam, so tests can make the bake return `CANCELLED` or raise at the operator boundary
  and assert that blocks, timestamp, fingerprint and status are unchanged. The
  post-bake fingerprint-mismatch branch is tested too: it marks the cache `OUTDATED` and does not
  pretend the old cache came back. This does *not* cover a real mid-write failure inside Blender's
  bake; a genuine I/O failure part-way through a bake remains unverified (no reliable way to force
  one from Python was found — a DISK bake into a blocked path still reports `FINISHED`).
- **Tests**: `tests/test_maintenance_phase1.py` (103 checks covering the areas above),
  `tests/runtime/` (viewport evaluation, secondary scene, clean ZIP install) and
  `tests/run_tests.ps1`, which runs all of them on Blender 5.2 and 5.3.
- **Operations stay in the active scene**: discovery, the render pre-flight check, the armature
  fallback and the Surface Deform ownership scan are all scoped to `scene.objects`, so a second
  scene's cages and binds are not baked or cleared.
- **Clear Cache leaves unrelated objects alone**: `giggle.clear_sim_cache` no longer strips bake
  metadata from an active object that is not one of the caches being cleared.

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
