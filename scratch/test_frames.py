import bpy
import mathutils

scene = bpy.context.scene
rig = bpy.data.objects.get("Kasumi_rig")
body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

vg = body.vertex_groups.get("Jiggle_Zone")
if vg:
    vg_idx = vg.index
    breast_verts = [v.index for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.5 for g in v.groups)]
    print(f"Found {len(breast_verts)} breast verts on body")
    
    for f in range(0, 15):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        b_eval = body.evaluated_get(dg)
        
        b_mat = b_eval.matrix_world
        b_pts = [b_mat @ b_eval.data.vertices[idx].co for idx in breast_verts[:50]]
        b_mean = sum(b_pts, mathutils.Vector((0,0,0))) / len(b_pts)
        
        if top:
            t_eval = top.evaluated_get(dg)
            t_mat = t_eval.matrix_world
            t_pts = [t_mat @ v.co for v in t_eval.data.vertices[:50]]
            t_mean = sum(t_pts, mathutils.Vector((0,0,0))) / len(t_pts)
            dist = (b_mean - t_mean).length
            print(f"Frame {f:2d}: Body Breast mean={b_mean}, Top mean={t_mean}, Dist={dist*100:.2f} cm")
        else:
            print(f"Frame {f:2d}: Body Breast mean={b_mean}")
