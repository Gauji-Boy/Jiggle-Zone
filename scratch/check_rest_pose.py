import bpy
import mathutils

rig = bpy.data.objects.get("Kasumi_rig")
body = bpy.data.objects.get("kasumi_body")
top = bpy.data.objects.get("top")

print("Checking Rest Pose vs Frame 1 pose...")
rig.data.pose_position = 'REST'
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)
t_eval = top.evaluated_get(dg)

# Check breast position in REST POSE
vg = body.vertex_groups.get("Jiggle_Zone")
vg_idx = vg.index
b_pts = [b_eval.matrix_world @ b_eval.data.vertices[v.index].co for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.5 for g in v.groups)]
b_mean_rest = sum(b_pts, mathutils.Vector((0,0,0))) / len(b_pts)

t_pts = [t_eval.matrix_world @ v.co for v in t_eval.data.vertices[:50]]
t_mean_rest = sum(t_pts, mathutils.Vector((0,0,0))) / len(t_pts)
print(f"REST POSE Breast mean: {b_mean_rest}, Top mean: {t_mean_rest}, Dist: {(b_mean_rest - t_mean_rest).length*100:.2f} cm")

# Now check FRAME 1 POSE
rig.data.pose_position = 'POSE'
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
b_eval = body.evaluated_get(dg)
t_eval = top.evaluated_get(dg)

b_pts_f1 = [b_eval.matrix_world @ b_eval.data.vertices[v.index].co for v in body.data.vertices if any(g.group == vg_idx and g.weight > 0.5 for g in v.groups)]
b_mean_f1 = sum(b_pts_f1, mathutils.Vector((0,0,0))) / len(b_pts_f1)
t_pts_f1 = [t_eval.matrix_world @ v.co for v in t_eval.data.vertices[:50]]
t_mean_f1 = sum(t_pts_f1, mathutils.Vector((0,0,0))) / len(t_pts_f1)
print(f"FRAME 1 Breast mean: {b_mean_f1}, Top mean: {t_mean_f1}, Dist: {(b_mean_f1 - t_mean_f1).length*100:.2f} cm")

# Check where the arms are in Rest vs Frame 1
pb_arm = rig.pose.bones.get("c_arm_fk.l")
if pb_arm:
    print(f"Bone c_arm_fk.l in Frame 1: loc={pb_arm.location}, rot={pb_arm.rotation_euler if pb_arm.rotation_mode == 'XYZ' else pb_arm.rotation_quaternion}")
