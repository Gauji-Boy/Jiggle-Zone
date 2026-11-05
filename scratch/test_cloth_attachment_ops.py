import bpy

body = bpy.data.objects.get('kasumi_body')
topcen = bpy.data.objects.get('topcen')
rig = bpy.data.objects.get('Kasumi_rig')

def eval_f1(label):
    bpy.context.scene.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg) if body else None
    t_ev = topcen.evaluated_get(dg) if topcen else None
    b_z = max(v.co.z for v in b_ev.data.vertices) if b_ev else 0
    t_z = max(v.co.z for v in t_ev.data.vertices) if t_ev else 0
    print(f"[{label}] body_max_z={b_z:.4f}, topcen_max_z={t_z:.4f}")

eval_f1("START")

# Test 1: fix_body_manifold
print("\n--- Testing fix_body_manifold ---")
bpy.context.view_layer.objects.active = body
body.select_set(True)
try:
    bpy.ops.giggle.fix_body_manifold()
except Exception as e:
    print("fix_body_manifold error:", e)
eval_f1("AFTER FIX_MANIFOLD")

# Test 2: rebind_clothing_modifiers
print("\n--- Testing rebind_clothing_modifiers ---")
bpy.ops.object.select_all(action='DESELECT')
for o in [body, topcen]:
    if o: o.select_set(True)
bpy.context.view_layer.objects.active = topcen
try:
    bpy.ops.giggle.rebind_clothing_modifiers()
except Exception as e:
    print("rebind error:", e)
eval_f1("AFTER REBIND")

# Test 3: copy_zone_to_clothing
print("\n--- Testing copy_zone_to_clothing ---")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = body
body.select_set(True)
topcen.select_set(True)
bpy.context.scene.giggle_settings.active_zone_index = 0
try:
    bpy.ops.giggle.copy_zone_to_clothing()
except Exception as e:
    print("copy_zone error:", e)
eval_f1("AFTER COPY_ZONE")
