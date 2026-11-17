# Jiggle Zone — 3.4.0

A high-performance Blender character secondary motion and XPBD soft-body simulation add-on.

## Requirements

- Blender 5.2 LTS or Blender 5.3 Beta (or newer).
- The bundled `assets/Wiggy_0.2.0.blend`, `assets/Wiggy_0.1.blend`, `assets/BackFaces.blend` and `assets/JiggleV2.blend` files must remain in the `assets/` directory next to `__init__.py`.

## Install

1. In Blender, open **Edit -> Preferences -> Get Extensions** (or **Add-ons**).
2. Click the dropdown arrow in the top right and select **Install from Disk...**
3. Select `jiggle-zone.zip`.
4. Enable **Jiggle Zone**.
5. In the 3D Viewport, open the **N-panel -> Jiggle Zone** tab.

## Upgrading from Giggle 2.x

Jiggle Zone 3.0.0 uses a new extension id, so Blender treats it as a different add-on.

1. Install `jiggle-zone.zip` **while Giggle Soft Body Physics 2.1 is still installed and enabled**.
2. Open each 2.x project once. Markers migrate and the panel settings copy across.
3. Save the project, then remove the old add-on.

Step 1 matters: Blender discards an unregistered property group when a file loads, so if you
remove 2.1 first, Jiggle Zone starts from its defaults for bake range, cache path and preset
selection. Those old values are not deleted from the file and remain readable by 2.1.

What does not carry over:

- The `Giggle_Proxies` collection is renamed to `Jiggle_Proxies`. Reopening a migrated file in
  2.1 will not find it, so proxies must be re-linked.
- `giggle.*` operators are gone with no alias. Keymaps and scripts must be rebound to `jiggle.*`.

## Quick Start

1. Select your character mesh and create a vertex group for the region to simulate (e.g., chest, glutes, belly).
2. Paint smooth weights on the intended vertices (soft falloffs produce the most natural elasticity).
3. In the Jiggle Zone panel under **Create New Zone**, select the vertex group and pick an anatomical preset.
4. Click **Add Jiggle Zone**.
5. By default, **Cage XPBD** is generated to provide 5x-10x faster playback. You can toggle between Cage XPBD and Full-Mesh XPBD at any time.

## Collider Back Faces (v3.4.0)

Closed colliders can leak: a garment inside a closed mesh may be pushed out through the side
facing away from the body. **Collider Back Faces** excludes the faces you choose without
touching the mesh.

1. Select the collider object, enter Edit Mode and select the faces to exclude.
2. Open **Collider Back Faces** in the sidebar and click **Mark Back Faces**.

- The filter is a `Back Faces` Geometry Nodes modifier placed directly before `Collider`. It
  writes the solver's own exclusion attribute, so the mesh, its vertices, vertex groups and
  the `Collider` modifier are never modified.
- **Clear Back Faces** removes only that modifier. Undo/redo covers both operators.
- The mask is stored per collider object and shared by every zone that uses it, so one
  collider behaves the same in all zones.
- Nothing runs automatically: marking is always an explicit action, and it invalidates the
  bake of every zone that references the collider.
- **Boundary colliders** (`Boundary` enabled) cannot be marked, because the boundary shell is
  what keeps the solver's cage closed.
- A mask addresses faces by index. The collider's topology is recorded exactly when you mark:
  every corner index, every face's corner count, and the face/loop/vertex/edge counts. Any change
  of face order or connectivity is therefore detected even when every count stays the same. The
  check runs before the next evaluation, so the old mask can never exclude the wrong faces, and
  the panel tells you to mark again. The mask is kept, so restoring the original topology
  re-enables it. Re-marking always replaces the stale mask.
- The safety scan finds the filter by its node group, so renaming the modifier cannot hide a
  stale mask. The per-update guard is enabled only when the open file actually contains a filter
  or its tracking data; a clean scene pays nothing.
- The filter fails closed: if the topology record is missing, was written by an older version, or
  the check itself cannot run, the filter is disabled rather than applied to faces the record
  cannot vouch for.
- Marking reads the live Edit Mode selection from the BMesh, and the mask is written against the
  mesh the modifier stack evaluates.
- Marking is refused on linked or overridden objects; make the object local first.

## Simulation Caching & Baking (v3.0.0)

- **Instant Scrubbing**: Click **Bake All Zones** to bake simulation state to `PACKED` (stored inside `.blend`) or `DISK` storage for non-sequential, instantaneous viewport scrubbing.
- **Dynamic Invalidation**: Changing physics parameters in the Jiggle Zone panel automatically flags the cache as `OUTDATED`. Click **Rebake All** to refresh.
- **Animation Changes**: When modifying character keyframe animation or editing raw Geometry Nodes modifier inputs directly in the Modifiers tab, click **Rebake All** to recompute the simulation.

## Clothing Attachment (v1.2.1)

- **Flush Surface Deform Proxy**: Binds clothes directly to character physics zones via clean, non-destructive deformation proxies.
- **Auto Zone Detection**: Automatically predicts and resolves the closest physics zone per-garment using geometry-aware surface proximity.
- **Clean Viewport**: Simulation cages and deformation proxies reside in a dedicated hidden collection to eliminate wireframe clutter.

## Compatibility Notes

- **Wiggy XPBD** is the default high-performance engine for creating new zones, and new zones use the bundled **Wiggy 0.2.0** solver group.
- Zones from earlier projects keep the solver group their file already contains: opening a 3.0.0 project does not inject or replace its `Wiggy 0.1` groups, and zones added afterwards use 0.2.0 alongside them.
- **Full-Mesh XPBD** remains fully supported as a hero-shot toggle.
- Existing **Jiggle V2** modifiers from v1.2.1 projects remain functional and retain their legacy dynamics controls.
