import bpy

body = bpy.data.objects['kasumi_body']
top = bpy.data.objects['topcen']
scene = bpy.context.scene

print('=== CHECKING KASUMI_BODY DEFORMATION ACROSS FRAMES ===')

for f in [1, 2, 3, 4, 5]:
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(dg)
    b_mesh = b_eval.to_mesh()
    
    # Vertices in jiggle zone
    v_breast = b_eval.matrix_world @ b_mesh.vertices[791].co
    # Vertices outside jiggle zone (e.g. nose / head)
    v_head = b_eval.matrix_world @ b_mesh.vertices[0].co
    
    print(f'Frame {f}: Breast=(z={v_breast.z:.4f}, y={v_breast.y:.4f}), Head=(z={v_head.z:.4f})')
    b_eval.to_mesh_clear()

print('\n=== NOW WITH GIGGLE MODIFIERS MUTED ===')
for m in body.modifiers:
    if m.type == 'NODES':
        m.show_viewport = False

for f in [1, 2, 3, 4, 5]:
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_eval = body.evaluated_get(dg)
    b_mesh = b_eval.to_mesh()
    v_breast = b_eval.matrix_world @ b_mesh.vertices[791].co
    v_head = b_eval.matrix_world @ b_mesh.vertices[0].co
    print(f'Frame {f} (Muted): Breast=(z={v_breast.z:.4f}, y={v_breast.y:.4f}), Head=(z={v_head.z:.4f})')
    b_eval.to_mesh_clear()
