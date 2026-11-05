"""Runtime checks that need a real scene loaded, run headless.

    blender -b <scene.blend> --python-exit-code 1 --python tests/runtime/test_viewport_qa.py

Unlike the earlier version of this script it exits non-zero on failure, and it measures the
evaluated mesh rather than the original data (a modifier cannot change `obj.data`, so reading it
reports zero drift no matter what the simulation does).
"""

import math
import sys
import time
import traceback

import bpy

FAILURES = []
NOTES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS", name)
    else:
        print("FAIL", name, detail)
        FAILURES.append(name)


def note(name):
    NOTES.append(name)
    print("NOT TESTED", name)


def evaluated_coord(obj, depsgraph, index=0):
    evaluated = obj.evaluated_get(depsgraph)
    return evaluated.data.vertices[index].co.copy()


def main():
    scene = bpy.context.scene
    print("BLENDER", bpy.app.version_string, "FILE", bpy.data.filepath)

    cage = bpy.data.objects.get("Chest_Cage")
    if cage is None:
        print("SKIP: no Chest_Cage in this scene; nothing to measure")
        sys.exit(0)

    depsgraph = bpy.context.evaluated_depsgraph_get()

    # 1. Rewind stability, measured on the evaluated cage.
    scene.frame_set(1)
    bpy.context.view_layer.update()
    first = evaluated_coord(cage, depsgraph)
    scene.frame_set(15)
    bpy.context.view_layer.update()
    bore = evaluated_coord(cage, depsgraph)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    again = evaluated_coord(cage, depsgraph)
    drift = (again - first).length
    moved = (bore - first).length
    print(f"   evaluated v0 frame1={tuple(round(v, 5) for v in first)} "
          f"frame15={tuple(round(v, 5) for v in bore)} drift={drift:.6f} moved={moved:.6f}")
    check("the simulation actually moves the evaluated mesh", moved > 1e-4, f"moved={moved:.6f}")
    check("rewind to frame 1 returns the evaluated mesh", drift < 1e-4, f"drift={drift:.6f}")

    # 2. Cost of an unbaked evaluation per frame. This is not viewport playback FPS.
    times = []
    for frame in range(1, 31):
        start = time.perf_counter()
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        coord = evaluated_coord(cage, depsgraph)
        times.append((time.perf_counter() - start) * 1000.0)
        check(f"frame {frame} has finite coordinates",
              all(math.isfinite(v) for v in coord), str(tuple(coord)))
    average = sum(times) / len(times)
    print(f"   unbaked evaluation {average:.1f} ms/frame (min {min(times):.1f}, max {max(times):.1f})")

    # 3. Followers bound to the cage.
    followers = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj == cage:
            continue
        for mod in obj.modifiers:
            if mod.type == 'SURFACE_DEFORM' and mod.target == cage:
                followers.append((obj.name, mod.is_bound))
    print("   followers:", followers)
    check("at least one follower is bound to the cage", bool(followers), str(followers))
    check("every follower reports is_bound", all(bound for _, bound in followers), str(followers))

    # 4. Cage XPBD state, and what else simulates the same body. Mixing a cage with a full-mesh
    #    zone is a design choice in this file, so it is reported, not failed.
    body = bpy.data.objects.get("kasumi_body") or bpy.data.objects.get("Kasumi_body")
    cage_mod = next((m for m in cage.modifiers
                     if m.type == 'NODES' and m.node_group and 'Wiggy' in m.node_group.name), None)
    check("the cage has a Wiggy modifier", cage_mod is not None)
    if cage_mod:
        check("the cage modifier is enabled in the viewport", cage_mod.show_viewport)
    if body:
        zones = [(m.name, m.show_viewport, m.show_render,
                  sum(len(b.data_blocks) for b in m.bakes))
                 for m in body.modifiers
                 if m.type == 'NODES' and m.node_group and 'Wiggy' in m.node_group.name]
        active = [z for z in zones if z[1] or z[2]]
        print("   body Wiggy zones (name, viewport, render, blocks):", zones)
        print("   active full-mesh zones on the body:", [z[0] for z in active])
        if active:
            print("   NOTE: this body runs a cage and full-mesh zones at the same time")
    else:
        note("full-mesh XPBD state (no kasumi_body in this scene)")

    note("interactive viewport feel, mouse interaction and playback smoothness (headless run)")

    print(f"RESULT {len(FAILURES)} failure(s)")
    if FAILURES:
        print("FAILED:", ", ".join(FAILURES))
        sys.exit(1)


try:
    main()
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    sys.exit(1)
