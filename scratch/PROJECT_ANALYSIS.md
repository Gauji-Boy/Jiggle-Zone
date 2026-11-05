# Giggle Soft Body Physics — Project Analysis

Date: 2026-11-05. Scope: `D:\Blender\Giggle` (add-on source, packaging, tests, repo state).

## 1. What this is

A Blender add-on (v2.0.0, requires Blender 5.2+) that adds XPBD soft-body / secondary-motion
simulation to characters: per-zone vertex groups, an auto-generated low-poly simulation cage
(`Armature -> Wiggy 0.1 Geometry Nodes -> Surface Deform` back onto the body), clothing that
follows the cage through deformation proxies, anatomical presets, and a bake/cache manager with
SHA-256 "dependency fingerprints" that mark caches `BAKED` / `OUTDATED` / `NOT_BAKED`.

### Shape of the code

| Item | Value |
| --- | --- |
| `giggle_addon/__init__.py` | 7,753 lines, 315 KB, single module |
| Classes | 56 (55 registered, `VIEW3D_PT_giggle_base` is a mixin) |
| Functions | 170 |
| RNA properties | 67 |
| `except` handlers | 108 — 80 of them silently `pass` |
| Largest methods | `attach_clothing_proxy.execute` 381 L, `generate_cage.execute` 256 L, `add_zone.execute` 157 L, main panel `draw` 155 L |
| Custom ID-props | 14 `_giggle_*` keys on objects |

Layout: `giggle_addon/` (source + assets), `scratch/` (126 one-off `.py` scripts, 6 logs),
`tasks/` (plan + todo), `backup_v121/`, `backup_v200_release/`, `giggle_backup/` (runtime
`.blend` copies). Total 1.67 GB, of which 1.46 GB is bake backups.

## 2. Verified current state

- Source, both extension installs (`5.2`, `5.3`) and the `5.2/scripts/addons` copy are
  byte-identical (same SHA-256).
- `giggle_addon.zip` is current: 6 entries, 1.9 MB, `giggle_addon/…` root, no `.pyc`.
- `bl_info` version `(2,0,0)` = manifest `version = "2.0.0"` = README heading.
- `scratch/test_milestone3_acceptance.py` passes on **Blender 5.3 Beta and 5.2.2 LTS**
  (exit 0, all assertions, only `Chest_Cage` discovered in the POC file). I ran both; it
  creates a 150 MB backup on each `rebake_all`.
- `regress_audit_52.log` / `regress_audit_53.log` show the maintenance suite passing on both.
- Installed `CHANGELOG.md` is **older** than the repo copy (sync script copies only
  `__init__.py`).

So the build is coherent and the Milestone-3 claims are actually testable and passing. That is
better than most add-on projects at this size.

## 3. Findings, in priority order

### 3.1 Backup growth is unbounded and mostly useless (highest impact)

`create_project_backup()` (`__init__.py:4913`) does `shutil.copy2` of the whole `.blend` into
`giggle_backup/` on **every** `rebake_all`, with no pruning, no dedupe, no setting.
Evidence: one 15-frame test run added two 150 MB files; the folder now holds 10 copies of the
same file (1.46 GB) — all with identical size and identical source mtime.

Two further problems:

- The copy is of the file **on disk**, not the in-memory state. Unsaved edits (the normal case
  while animating) are not in the backup, so it does not protect what the user is about to lose.
- Only `rebake_all` takes a backup (`:5204`). `bake_all_cages`, `bake_selected_cage` and
  `bake_missing` do not, although they purge caches too — the "transactional" guarantee is
  inconsistent across the four operators.

### 3.2 The bake is destructive before it can succeed

`execute_cage_bake_step` (`:4933`) deletes the existing cache
(`simulation_nodes_cache_delete`, `:4939`) *before* baking. If the bake operator fails or
produces zero blocks, the previous cache is already gone and the code only marks `FAILED`.
"A recoverable backup is created before cache modification" is only true for one entry point,
and the backup (3.1) is a stale file copy.

### 3.3 "Strict target isolation" rests on name heuristics

`get_giggle_simulation_objects` (`:4773`) treats a mesh as Giggle-managed if it **has the
`_giggle_cage` prop OR its name ends with `_Cage` OR it sits in a collection literally named
`Giggle_Cages`**, plus a modifier whose node group is *named* `Wiggy 0.1`. Consequences:

- A user's own object called `Hair_Cage` with their own Wiggy setup is picked up by
  `bake_all`, `clear_sim_cache` and the render pre-check — the exact opposite of the
  "unrelated simulations are completely protected" claim.
- A renamed `Wiggy 0.1` node group silently makes every zone invisible to the manager.
- `get_driving_armature:4644` falls back to *any* armature with an action in the file, so in a
  multi-character scene a cache can be fingerprinted against the wrong rig.

Fix is cheap and removes all three: stamp one authoritative `_giggle_managed = 1` prop at
creation, look up the node group by asset identity rather than name, and drop the `_Cage`
suffix test.

### 3.4 The fingerprint has real blind spots

`compute_animation_hash` (`:4650`):

- Hashes `act.name`, so renaming an action (cosmetic) invalidates every cache.
- Reads only `arm.animation_data.action` — **object-level transform animation, NLA strips,
  drivers and shape keys are not covered**. Sliding an armature object along the timeline
  leaves the cache marked `BAKED`.
- Doesn't include scene frame range for the animation domain (it's in the simulation hash, OK),
  but also ignores `action_slot`/slot assignment.

`compute_geometry_hash` (`:4709`) hashes cage vertices and the source vertex-group weights, but
not the source body mesh. Editing the body (the thing the cage is bound to via Surface Deform)
does not invalidate.

`_giggle_bake_schema_version` is written (`:4764`) and **never read**, so a future hashing
change cannot be distinguished from a stale cache.

### 3.5 The wardrobe "cache" recomputes its own key at O(all objects) per redraw — measured, not a problem

`get_wardrobe_scene_collections` (`:6249`) is called from
`VIEW3D_PT_giggle_wardrobe.draw` (`:7180`) on every redraw, and its validity key walks every
collection and every object (`:6260-6269`). Measured on the POC scene (176 objects, 9
collections): 0.2 ms per call. That is fine at this size, so this is a design smell (the cache
key costs as much as the query it guards) rather than a bug. It would only matter at several
thousand objects.

### 3.6 Silent failure is the default

80 of 108 handlers are `except Exception: pass`. Notably around cache deletion, unregister, and
the bake path — the places where a swallowed error turns into a wrong status in the UI. The
`scratch/error.log` (`StructRNA of type Object has been removed`) is the visible tip of this
pattern.

### 3.7 The render pre-flight warning is invisible

`render_pre_cache_check` (`:7630`) prints to the console only. In a normal GUI render the
console is not open; in background renders nobody reads it. It also recomputes the full
fingerprint (all keyframes + all cage verts + all body weights + all bone rest data) for every
cage at render start, inside a blanket `try/except: pass`.

### 3.8 Structure and process

- Single 315 KB module with no package split; 381-line operator bodies; 16 operators with no
  `poll()`, so they rely entirely on in-`execute` guards.
- Presets are mutated at import time (`:2324-2356`), including regex passes that rewrite
  user-visible names and descriptions. Runtime behaviour depends on module import order.
- **No version control anywhere** in `D:\Blender\Giggle`. History lives in `backup_v121/`,
  `backup_v200_release/` zips and a pile of `apply_v121_*.py` / `patch_init.py` string-replacement
  scripts that rewrite `__init__.py` in place with `assert`-guarded `str.replace`.
- `scratch/` holds 126 scripts, many near-duplicates (`check_frame1`, `check_f1_exact`,
  `check_proxy_full`, `check_proxy_arm`, `test_steps`, `test_step_by_step`, five `quick_test*`).
  The only runner is `runner.py`, which `exec()`s another script and writes failures to
  `error.log`. There is no test suite in the package, no CI, no `requirements.txt`.
- Packaging: the zip root is `giggle_addon/` while the manifest id is `giggle_physics`; the
  installed extensions are `giggle_physics/`. Worth confirming on a clean machine that
  "Install from Disk" accepts the mismatch, since that is the documented install path.

## 4. What is already good

- The cage architecture is the right call: ~485 simulated verts instead of the full body, with a
  legacy full-mesh path preserved and no forced migration.
- Fingerprinting by domain with a stored reason string is a sound design; the panel reads cached
  props (0.001 ms) rather than hashing during redraw (`:6034`).
- Clothing attachment does genuine transactional staging (verify bindings, then delete old
  proxy) and restores context/mode.
- CHANGELOG and README are specific and honest about calibration limits; the acceptance test
  actually asserts state transitions instead of printing "OK".
- Guards in `draw()` are consistent, which keeps a single bad datablock from breaking panels.

## 5. Suggested order of work (small, reversible)

1. **Backups**: keep the newest 2, skip when the source file is unchanged since the last
   backup, add a size setting, and apply the same policy to all four bake operators — or drop
   file copies entirely and rely on `bpy.data` snapshot + undo.
2. **Bake order**: bake first, purge after success; or purge into a temp target so a failed bake
   leaves the previous cache intact.
3. **Identity**: replace the `_Cage` / `Giggle_Cages` / `Wiggy 0.1`-name heuristics with
   `_giggle_managed` + node-group asset reference; remove the "any armature" fallback.
4. **Fingerprint**: drop `act.name`; add object-level fcurves, NLA and shape keys; hash the body
   mesh bounds/vertex count; compare `_giggle_bake_schema_version` to `FINGERPRINT_SCHEMA`.
5. **Wardrobe**: invalidate on `depsgraph_update_post` with a dirty flag (or a 0.25 s
   `bpy.app.timers` throttle) instead of rebuilding a full signature per redraw.
6. **Pre-flight**: make it actionable — status-bar message plus an optional abort, and skip the
   deep hash when the cheap `get_cage_bake_status` already says `NOT_BAKED`.
7. **Repo**: `git init`, move `scratch/` tests into `tests/`, delete the one-offs, keep two
   headless suites (maintenance + milestone) and one `run_tests.ps1` for 5.2/5.3.
8. Only then consider splitting `__init__.py` into `presets.py`, `physics.py`, `baking.py`,
   `clothing.py`, `ui.py` — the split is valuable but is a mechanical, high-diff change that is
   much safer once history exists.

## 6. Loose ends I did not resolve

- I did not verify whether Blender's extension installer accepts a zip whose root folder name
  differs from `manifest.id`.
- I did not measure fingerprint cost on a real production-file render; the concern is from code
  shape, not a profile.
- I did not run the clothing/wardrobe paths, which need a scene with garments and proxies.
