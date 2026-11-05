# Changelog

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
