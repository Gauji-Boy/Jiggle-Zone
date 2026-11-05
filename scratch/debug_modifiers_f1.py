import bpy

body = bpy.data.objects.get("kasumi_body")
vg = body.vertex_groups.get("Jiggle_Zone")
vg_idx = vg.index
b_v_idx = [v.index for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.8 for g in v.groups)][0]

print(f"Tracking body vertex {b_v_idx}...")

for f in [1, 2]:
    print(f"\n=== FRAME {f} ===")
    bpy.context.scene.frame_set(f)
    
    # Check with no modifiers
    for m in body.modifiers:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(dg)
    print(f"  Base (no mods): {b_eval.matrix_world @ b_eval.data.vertices[b_v_idx].co}")
    
    # Enable modifiers one by one
    for m in body.modifiers:
        m.show_viewport = True
        dg = bpy.context.evaluated_depsgraph_get()
        b_eval = body.evaluated_get(dg)
        print(f"  After '{m.name}' ({m.type}): {b_eval.matrix_world @ b_eval.data.vertices[b_v_idx].co}")
