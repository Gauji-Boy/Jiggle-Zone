import bpy

body = bpy.data.objects.get('kasumi_body')
for m in list(body.modifiers):
    if m.name == 'Test_Move':
        body.modifiers.remove(m)

# Test A: NODES mod without node group
modA = body.modifiers.new(name="Test_Empty", type='NODES')
with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=modA.name, index=1)
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
print("Test A (Empty NODES mod at idx 1) Frame 1: max_z =", max(v.co.z for v in body.evaluated_get(dg).data.vertices))
body.modifiers.remove(modA)

# Test B: What if Wiggy 0.1 is at index 1:
modB = body.modifiers.new(name="Test_Wiggy", type='NODES')
modB.node_group = bpy.data.node_groups.get("Wiggy 0.1")
with bpy.context.temp_override(active_object=body, object=body):
    bpy.ops.object.modifier_move_to_index(modifier=modB.name, index=1)

print("\nTesting frames with Test_Wiggy at idx 1:")
for f in [1, 2, 3, 1]:
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    b_ev = body.evaluated_get(dg)
    print(f"  Frame {f}: max_z = {max(v.co.z for v in b_ev.data.vertices)}")

# Test C: What is inside Wiggy 0.1 that causes Frame 1 to be rest pose?
# Check the modifier's sockets / inputs
print("\nTest_Wiggy inputs:")
for k in modB.keys():
    print(f"  {k} = {modB[k]}")

body.modifiers.remove(modB)
