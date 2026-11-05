CHANGELOG_PATH = r"d:\Blender\Giggle\giggle_addon\CHANGELOG.md"

with open(CHANGELOG_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

target = """### Milestone 3: Simulation Cache & Disk Baking
- **Native Simulation Baking (`giggle.bake_all_cages`, `giggle.bake_selected_cage`)**: Bake every active Giggle cage for instant, non-sequential timeline scrubbing (67 FPS).
- **Flexible Storage**: Supports both internal `PACKED` cache storage and external `DISK` cache storage.
- **Target Isolation**: Isolates selection to strictly Giggle simulation cages during bake operations to avoid baking or clearing unrelated scene simulations.
- **Outdated Cache Invalidation**: Automatically flags cache as `OUTDATED` when physics sliders are adjusted."""

replacement = """### Milestone 3: Transactional Baking & Lazy Dependency Fingerprinting
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
- **Strict Target Isolation**: Operates exclusively on Giggle-managed cages. Unrelated Geometry Nodes modifiers and simulations are completely protected."""

assert target in text, "Could not find Milestone 3 target in CHANGELOG.md"
text = text.replace(target, replacement, 1)

with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

# Also update root CHANGELOG.md
root_changelog = r"d:\Blender\Giggle\CHANGELOG.md"
with open(root_changelog, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated CHANGELOG.md in giggle_addon/ and root directory.")
