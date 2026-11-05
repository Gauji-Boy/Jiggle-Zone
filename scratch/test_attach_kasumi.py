import bpy
import mathutils

# Let's inspect Kasumi_rig action at frame 1 vs frame 2 vs frame 0
rig = bpy.data.objects.get("Kasumi_rig")
body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

print("Kasumi_rig pose bones at frame 0, 1, 2:")
for f in [0, 1, 2]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    r_eval = rig.evaluated_get(dg)
    for b in ["c_arms_fk.l", "c_hand_fk.l", "c_spine_02.x", "c_breast_01.l"]:
        pb = r_eval.pose.bones.get(b)
        if pb:
            print(f"Frame {f} bone {b} head: {r_eval.matrix_world @ pb.head}")

# Now let's test running giggle.attach_clothing_proxy on top and kasumi_body
bpy.ops.object.select_all(action='DESELECT')
top.select_set(True)
bpy.context.view_layer.objects.active = body
body.select_set(True)

print("\nRunning giggle.attach_clothing_proxy...")
res = bpy.ops.giggle.attach_clothing_proxy()
print(f"Attach result: {res}")

# Now let's check distance between body breasts and top across all frames 1 to 33!
vg = body.vertex_groups.get("Jiggle_Zone")
vg_idx = vg.index
breast_verts = [v.index for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.5 for g in v.groups)]

# Let's also find the closest top vertices to breast verts at bind frame (frame 1)
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)
t_eval = top.evaluated_get(dg)

b_mat = b_eval.matrix_world
t_mat = t_eval.matrix_world

# Find 10 pairs of corresponding vertices
pairs = []
for b_idx in breast_verts[::30]:
    b_pt = b_mat @ b_eval.data.vertices[b_idx].co
    min_d = 999.0
    best_t_idx = -1
    for t_idx, tv in enumerate(t_eval.data.vertices):
        d = (b_pt - (t_mat @ tv.co)).length
        if d < min_d:
            min_d = d
            best_t_idx = t_idx
    pairs.append((b_idx, best_t_idx, min_d))

print(f"Sample pairs at Frame 1 (min distance at bind): {[round(p[2]*100, 3) for p in pairs]} cm")

print("\nTracking distances across all frames 1..33:")
for f in range(1, 34):
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(dg)
    t_eval = top.evaluated_get(dg)
    
    b_mat = b_eval.matrix_world
    t_mat = t_eval.matrix_world
    
    dists = []
    for b_idx, t_idx, _ in pairs:
        pt_b = b_mat @ b_eval.data.vertices[b_idx].co
        pt_t = t_mat @ t_eval.data.vertices[t_idx].co
        dists.append((pt_b - pt_t).length)
    
    avg_d = sum(dists) / len(dists)
    max_d = max(dists)
    print(f"Frame {f:2d}: avg={avg_d*100:6.3f} cm, max={max_d*100:6.3f} cm, diff_from_bind={(avg_d - pairs[0][2])*100:6.3f} cm")
