# Repo audit — Giggle Soft Body Physics

Run 2026-11-05 against `D:\Blender\Giggle` (source v2.0.0, Blender 5.2/5.3).

**What this repo does:** a Blender add-on that adds XPBD jiggle and soft-body motion to
characters. It builds a small simulation cage from a vertex group, binds the body to it with
Surface Deform, makes clothes follow through hidden proxies, and bakes Simulation Zone caches
with SHA-256 fingerprints that report BAKED / OUTDATED / NOT_BAKED.
Load assumed: one artist, one `.blend` at a time, 1–4 zones, 1–300 frames, and a few people
installing the zip. Not a server, no concurrency.

## Must fix

1. **A longer frame range or a different cache storage never invalidates the bake**
   (`giggle_addon/__init__.py:4866-4868`)
   - **What this is:** `check_cage_validity` recomputes the fingerprint with the frame range
     and storage mode it just read back from the object.
   - **Problem:** both sides of the comparison use the stored values, so this part always
     matches. Measured: baked frames 1–15, set scene end to 60 → `BAKED`; switched storage to
     DISK → `BAKED`, while the modifier's `bake_target` was still `PACKED`. The same block also
     stores `_giggle_bake_schema_version` (`:4608`, `:4764`) and nothing ever reads it, so a
     cache written by an older fingerprint layout is judged with today's layout.
   - **Fix:** pass the requested `f_start`, `f_end` and `bake_storage_mode` into
     `compute_zone_fingerprint` and compare against the stored values. Reject the cache when
     `_giggle_bake_schema_version != FINGERPRINT_SCHEMA`.
   - **If we skip it:** "Bake Missing" skips the extra frames and the wrong storage, and
     playback past frame 15 runs live under a green "BAKED" badge.

2. **Rebake deletes the old cache before the new one is proven** (`__init__.py:4937-4941`)
   - **What this is:** `execute_cage_bake_step` calls `simulation_nodes_cache_delete` first,
     inside `except: pass`, then bakes.
   - **Problem:** if the bake fails or produces zero blocks, the previous working cache is
     already gone. The only fallback is the file copy from finding 3, which does not contain
     unsaved edits.
   - **Fix:** delete the pre-delete call. Measured: Blender re-bakes over an existing cache (an
     in-place bake with changed physics reproduced the clean-bake result), so the old cache
     survives a failed bake without any extra machinery.
   - **If we skip it:** one bad bake at frame 12 of 200 costs the artist the whole cache.

3. **Every Rebake All writes a full copy of the .blend and never cleans up**
   (`__init__.py:4913-4930`, called at `:5204`)
   - **What this is:** `create_project_backup` copies the `.blend` into `giggle_backup/` on each
     rebake, with no pruning and no setting.
   - **Problem:** one 150 MB copy per click. The folder now holds 10 copies (1.46 GB) — 6 of
     them from my three test runs today. It copies the file on disk, not the open scene, so the
     "safety backup" protects stale data. Only 1 of the 4 bake operators does it at all.
   - **Fix:** keep the newest file only, skip when the source has not changed, and apply the same
     rule to every bake operator (or drop the copy and rely on Blender's undo).
   - **If we skip it:** large projects fill the disk, and the copy gives false confidence.

4. **The animation fingerprint misses NLA and shape keys** (`__init__.py:4650-4659`)
   - **What this is:** it hashes one datablock, `arm.animation_data.action`.
   - **Problem:** when the rig's action is pushed to an NLA strip, `action` is `None` and the
     hash becomes `"NO_ACTION"` forever. Shape-key animation is never hashed. Animating either
     leaves the cache marked `BAKED`.
   - **Fix:** include NLA strips (name, action, range) and the shape-key action in the hash.
   - **If we skip it:** skin and cloth keep an old sim while the UI says it is current.

5. **Renaming an action invalidates every cache** (`__init__.py:4661`)
   - **What this is:** the action's *name* is hashed.
   - **Problem:** rename "Walk" to "Walk_final" and every zone goes `OUTDATED` — a full rebake
     for a cosmetic edit.
   - **Fix:** delete `h.update(act.name.encode('utf-8'))`.
   - **If we skip it:** artists learn to ignore the OUTDATED badge, which is the one warning that
     matters.

6. **"Clear Cache" can delete someone else's simulation** (`__init__.py:4773-4786`)
   - **What this is:** discovery accepts any mesh whose name ends in `_Cage`, or that sits in a
     collection called `Giggle_Cages`, plus a modifier whose node group is *named*
     `Wiggy 0.1`.
   - **Problem:** this add-on is a fork of Wiggy, so an unrelated Wiggy user has exactly that
     node group. A user object named `Hair_Cage` with their own Wiggy modifier is treated as
     Giggle-owned: Clear Cache deletes its bake and Bake All rebakes it.
   - **Fix:** one `_giggle_managed` flag stamped at creation, node group matched by datablock,
     and drop the suffix and collection-name tests.
   - **If we skip it:** the "Unrelated simulations preserved" message is false and another
     add-on's cache disappears.

7. **Re-attaching clothes keeps the old zone physics** (`__init__.py:6666-6680`)
   - **What this is:** a proxy is reused when body name, vertex count and vertex-group name
     match.
   - **Problem:** zone parameters are not checked. Change softness 0.2 → 0.9 and attach again;
     the garment follows a proxy still on 0.2, so cloth and skin move differently. Repainting
     weights with the same vertex count does the same.
   - **Fix:** store a hash of the zone sockets and weights on the proxy and require it, or rebuild
     when the source modifier changed.
   - **If we skip it:** clothing quietly stops matching the body, which the changelog promises it
     never does.

8. **Cages made before 2.0 are hashed without their body link** (`__init__.py:4718-4732`)
   - **What this is:** the geometry hash only covers body weights when `_giggle_source_body`
     exists.
   - **Problem:** the project's own POC cage does not have that property (checked), and 1.2
     projects are supported. Repainting chest weights in such a file leaves the cache `BAKED`.
   - **Fix:** find the body through the Surface Deform target or vertex-group name, or stamp the
     link the first time a legacy cage is used. While there, hash the weight at higher precision:
     it is rounded to 3 decimals (`:4730`), so repaints that move a vertex by under 0.0005 are
     invisible; cage coordinates are rounded to 4 (`:4717`). Use `repr`/full float text for both.
   - **If we skip it:** the most common edit on an old project is invisible to the cache check.

9. **The render warning cannot be seen** (`__init__.py:7630-7652`)
   - **What this is:** a `render_pre` handler that prints a warning to the console.
   - **Problem:** the console is closed during a normal render and nobody reads stdout in a
     background render. The whole handler also sits inside `except: pass`.
   - **Fix:** report through the window manager or cancel the render when the setting says
     strict, and remove the blanket except.
   - **If we skip it:** a stale-cache render produces no visible warning.

10. **The preset gravity reset is written to a dict nobody reads**
    (`__init__.py:2331-2343`)
    - **What this is:** import-time composition of `PRESETS`.
    - **Problem:** line 2336 replaces `PRESETS[k]['values']` with a new dict, but lines
      2341-2343 keep writing `Socket_5`, `Socket_3`, `Socket_67` into the old dict, which is now
      unreachable. Case: "Water Balloon" enables gravity (line 1157); the next recipe that omits
      `Socket_5` leaves gravity on and the zone drifts.
    - **Fix:** write those three keys into `_combined_values` before assigning it.
    - **If we skip it:** presets leak state — exactly what this block was added to prevent.

11. **Remove Zone leaves the hidden proxy behind** (`__init__.py:4181-4194`)
    - **What this is:** removal deletes the cage and the body's Surface Deform.
    - **Problem:** it never deletes `<body>_<vg>_Proxy`, which keeps its own copy of the sim.
      Re-add the zone with the same vertex group and the old proxy is reused (finding 7) with
      the old settings.
    - **Fix:** delete the proxy and its mesh during removal.
    - **If we skip it:** hidden objects pile up and re-added zones behave inconsistently.

12. **Any node group named "Wiggy 0.1" is trusted** (`__init__.py:2652-2654`)
    - **What this is:** `ensure_nodetree` returns whatever already has that name.
    - **Problem:** a user who owns the original Wiggy add-on has a `Wiggy 0.1` with different
      sockets; presets then do nothing (`set_mod_socket` returns False) with no message. If
      Blender renames the appended copy to `Wiggy 0.1.001`, `is_giggle_modifier` (`:2775`)
      stops recognising the modifier and the zone vanishes from the bake list.
    - **Fix:** version the node group and match modifiers by pointer, not by name.
    - **If we skip it:** silent no-op presets, or zones that disappear from the cache UI.

13. **The tests live outside the repo and nothing runs them** (`scratch/`, 126 `.py` files)
    - **What this is:** the cache manager's only test is
      `scratch/test_milestone3_acceptance.py`, run by hand against
      `D:\Blender\Giggle\poc_cage_xpbd_kasumi.blend`.
    - **Problem:** it is not in the package, there is no git repo, no CI and no runner, so no
      change re-runs it. 126 loose scripts sit next to it, many near-duplicates. I ran it by
      hand and it wrote 900 MB of backups.
    - **Fix:** a `tests/` folder with that file plus a `run.ps1` for 5.2 and 5.3; delete the
      one-off scripts.
    - **If we skip it:** the next regression is found by an artist.

14. **Withdrawn — the rebind double call is correct** (`__init__.py:6510-6524`)
    - **Why it was raised:** `if mod.is_bound: bind` looked like the same call twice.
    - **Correction:** `object.surfacedeform_bind` is a toggle. Tested in Blender 5.3: four calls
      in a row leave `is_bound` at True, False, True, False. The first call unbinds, the second
      rebinds. The same pattern is correct for Mesh Deform and Corrective Smooth.
    - **Action:** none. Do not "simplify" this.

19. **Rig constraints are hashed by type only, so retargeting one keeps the cache** (`__init__.py:4680-4684`)
    - **What this is:** the armature hash adds `bone:constraint_type:mute:influence` and nothing else.
    - **Problem:** target, subtarget, space and limits are not in the hash. Case: a Copy Rotation
      constraint on the chest bone is pointed at a different empty, or a Limit Rotation's max is
      changed; the pose changes, the simulation changes, the hash does not, so the zone stays
      `BAKED` and playback shows the old sim.
    - **Fix:** hash the constraint's own settings and its target datablock name, or simply drop the
      constraint loop and say constraints are outside the fingerprint (then do not claim rig
      dependencies are covered).
    - **If we skip it:** a rig change after bake silently plays a cache made for the old rig.

20. **Every scene's objects are treated as the current scene's zones** (`__init__.py:4776`)
    - **What this is:** discovery walks `bpy.data.objects`, which is the whole file, not
      `context.scene`.
    - **Problem:** a `.blend` with a second scene (props, a turntable, an old shot) that contains
      a `_Cage` mesh with a Wiggy modifier is included in Bake All and in Clear Cache from the
      character scene. Objects that are not linked to any scene are included too. The POC file has
      one scene, so this does not show up there — it needs a two-scene file.
    - **Fix:** iterate `context.scene.objects` in `get_giggle_simulation_objects`; reach other
      scenes only through an explicit "this scene" toggle.
    - **If we skip it:** clicking Bake All in one scene bakes another scene's cages, and Clear
      Cache deletes their caches.

## Nice to have

15. **Four bake operators are near copies** (`__init__.py:4987-5350`)
    - **What this is:** bake-all, bake-selected, rebake-all and bake-missing repeat the same ~50
      lines of settings, selection capture, `finally` restore and reporting.
    - **Problem:** they have already drifted: only `rebake_all` backs up, and the messages
      differ.
    - **Fix:** one `_run_bake(context, targets, make_backup)` helper and four thin operators.
    - **If we skip it:** every fix is made four times and one copy gets missed. About 180 lines.

16. **Dead helper** (`__init__.py:6342-6345`)
    - **What this is:** `find_character_clothing_collections` wraps the wardrobe lookup.
    - **Problem:** no caller anywhere in source, tests or backups (grep).
    - **Fix:** delete it.
    - **If we skip it:** nothing breaks; it just costs reading time.

17. **Weights are read by throwing an exception per unweighted vertex**
    (`__init__.py:4726-4730`)
    - **What this is:** `vg.weight(v.index)` inside `try` for every body vertex.
    - **Problem:** Blender raises `RuntimeError` for each vertex not in the group. Measured on
      50k verts: 0.076 s with exceptions vs 0.030 s reading `v.groups`. A 500k-vert body adds
      ~0.8 s per fingerprint, and one bake computes up to three of them.
    - **Fix:** loop `v.groups` and read the weight where `g.group == vg.index`.
    - **If we skip it:** bake prep slows down as meshes get denser.

18. **Clear Cache edits the active object even when it has no cache**
    (`__init__.py:5441-5448`)
    - **What this is:** after the loop it pops every bake property from `context.active_object`.
    - **Problem:** a full-mesh zone with a muted modifier is not discovered, so the props are
      cleared while the cache stays. The UI then says `NOT_BAKED` with a cache present.
    - **Fix:** delete the block; the loop already covers every discovered object.
    - **If we skip it:** wrong status after a mute/clear cycle.

**Verdict:** fix 1–3 first. Finding 1 makes the cache status lie, findings 2 and 3 lose work.

**Lean:** -190 lines, -0 dependencies possible.

**Second pass (2026-11-05, after a third-party review):**
- Finding 14 was wrong and is withdrawn: `object.surfacedeform_bind` is a toggle, measured in
  Blender 5.3 (four calls → bound, unbound, bound, unbound). The double call is intentional.
- ZIP install is settled, not a defect: installing `giggle_addon.zip` headless reported
  `STATUS Reinstalled "giggle_physics"` / `{'FINISHED'}`, and the installed `__init__.py` is
  byte-identical to the source. The nested `giggle_addon/` folder is accepted.
- Added finding 19 (rig constraints barely hashed), finding 20 (discovery is file-wide), the
  schema-version check in finding 1, and the hash precision in finding 8.

**Not checked:** clothing attach and the wardrobe UI in a live session with garments (no garment
scene); DISK-storage cleanup of files on disk; the ~2,000 lines of preset data; findings 19 and 20
come from reading the code, not from a live repro (there is no two-scene file and no retargeted
rig here).
Measured and fine: status reads are free, fingerprint is 0.15–0.22 s per cage on the POC file,
wardrobe lookup is 0.2 ms on 176 objects.

**Status after maintenance phase 1 (2026-11-05):**
- Fixed: 1 (range, storage, schema), 2 (no pre-delete; failed bake keeps the old cache),
  3 (one backup kept, no copy when the file did not change, live session written when unsaved),
  6 (ownership flag plus a Surface Deform proof, name and collection rules dropped),
  18 (Clear Cache no longer strips metadata from an unrelated active object),
  20 (discovery, render check, armature fallback and bind scan are scene-scoped).
- Backups now run from all four cache-replacing operators (`bake_all`, `bake_selected`,
  `rebake_all`, `bake_missing`) and only when a cache is actually about to be replaced.
- Tests: `tests/test_maintenance_phase1.py` (40 checks) passes on Blender 5.2.2 LTS and
  5.3.0 Beta, and `scratch/test_milestone3_acceptance.py` still passes on both.
- Test limitation (finding 2): a bake that fails *after* it has started writing cannot be forced
  from Python — a DISK bake into a directory whose parent is a file, and a bake started in edit
  mode, both return success (the edit-mode one even appends a second block set). What is proven
  is that the code no longer deletes the cache first (checked against the source) and that a bake
  which fails on a missing/broken modifier leaves the previous blocks, stamp and status intact.
- Test limitation (finding 3): `bpy.data.is_dirty` is always `False` in a background session
  (measured: unchanged after adding objects, moving them, writing custom properties and changing
  frames), so the test passes the dirty flag in explicitly through `create_project_backup(dirty=)`.
  `bake_all` on the POC file does take the dirty path in practice — the file loads dirty — and its
  backup open-s and contains the cage with its 20 cache blocks.
- Not yet fixed: 4, 5, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 19.
