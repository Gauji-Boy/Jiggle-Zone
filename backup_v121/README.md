# Giggle Soft Body Physics — 1.2.1

A Blender character-secondary-motion add-on using the bundled Wiggy XPBD Geometry Nodes group.

## Requirements

- Blender 5.2 or newer.
- The bundled `assets/Wiggy_0.1.blend` and `assets/JiggleV2.blend` files must remain in the `assets/` directory next to `__init__.py`.

## Install

1. In Blender, open **Edit → Preferences → Get Extensions** (or **Add-ons**, depending on the Blender build).
2. Use **Install from Disk** and select `giggle_addon.zip`.
3. Enable **Giggle Soft Body Physics**.
4. In the 3D Viewport, open the **N-panel → Giggle** tab.

## First simulation

1. Select a character mesh and create a vertex group for the region to simulate.
2. Paint non-zero weights on the intended vertices. Blend the weights at the boundary rather than using a hard binary mask.
3. In **Create New Zone**, select that group and choose a preset. New zones use **Wiggy XPBD**.
4. Click **Add Jiggle Zone**. The add-on places the modifier after armature deformation and before later surface finishing modifiers where possible.
5. Start playback from the scene start frame to evaluate the simulation. If you change important solver settings, reset/restart the simulation from the beginning.

## Clothing Attachment (v1.2.1)

- **Flush Surface Deform Proxy**: Binds clothes directly to character physics zones via clean, non-destructive deformation proxies.
- **Auto Zone Detection**: Automatically predicts and resolves the closest physics zone per-garment using geometry-aware surface proximity and character scale awareness.
- **ACID Transactional Integrity**: Staged modifiers, verified dependent garment migration, and complete rollback on any failure ensure existing scene setups and proxies are never corrupted.
- **Clean Viewport**: Deformation proxies reside in a dedicated hidden collection to eliminate wireframe cages and viewport clutter.

## Compatibility notes

- **Wiggy XPBD** is the supported engine for creating new zones and applying the reworked preset library.
- Existing **Jiggle V2** modifiers are retained for legacy projects and keep their basic dynamics controls.
