# Giggle Soft Body Physics — 2.1.0

A high-performance Blender character secondary motion and XPBD soft-body simulation add-on.

## Requirements

- Blender 5.2 LTS or Blender 5.3 Beta (or newer).
- The bundled `assets/Wiggy_0.1.blend` and `assets/JiggleV2.blend` files must remain in the `assets/` directory next to `__init__.py`.

## Install

1. In Blender, open **Edit -> Preferences -> Get Extensions** (or **Add-ons**).
2. Click the dropdown arrow in the top right and select **Install from Disk...**
3. Select `giggle_addon.zip`.
4. Enable **Giggle Soft Body Physics**.
5. In the 3D Viewport, open the **N-panel -> Giggle** tab.

## Quick Start

1. Select your character mesh and create a vertex group for the region to simulate (e.g., chest, glutes, belly).
2. Paint smooth weights on the intended vertices (soft falloffs produce the most natural elasticity).
3. In the Giggle panel under **Create New Zone**, select the vertex group and pick an anatomical preset.
4. Click **Add Jiggle Zone**.
5. By default, **Cage XPBD** is generated to provide 5x-10x faster playback. You can toggle between Cage XPBD and Full-Mesh XPBD at any time.

## Simulation Caching & Baking (v2.1.0)

- **Instant Scrubbing**: Click **Bake All Zones** to bake simulation state to `PACKED` (stored inside `.blend`) or `DISK` storage for non-sequential, instantaneous viewport scrubbing.
- **Dynamic Invalidation**: Changing physics parameters in the Giggle panel automatically flags the cache as `OUTDATED`. Click **Rebake All** to refresh.
- **Animation Changes**: When modifying character keyframe animation or editing raw Geometry Nodes modifier inputs directly in the Modifiers tab, click **Rebake All** to recompute the simulation.

## Clothing Attachment (v1.2.1)

- **Flush Surface Deform Proxy**: Binds clothes directly to character physics zones via clean, non-destructive deformation proxies.
- **Auto Zone Detection**: Automatically predicts and resolves the closest physics zone per-garment using geometry-aware surface proximity.
- **Clean Viewport**: Simulation cages and deformation proxies reside in a dedicated hidden collection to eliminate wireframe clutter.

## Compatibility Notes

- **Wiggy XPBD** is the default high-performance engine for creating new zones.
- **Full-Mesh XPBD** remains fully supported as a hero-shot toggle.
- Existing **Jiggle V2** modifiers from v1.2.1 projects remain functional and retain their legacy dynamics controls.
