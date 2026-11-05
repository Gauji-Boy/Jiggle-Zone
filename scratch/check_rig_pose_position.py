import bpy

autosave_path = r"C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_28620_autosave.blend"

body = bpy.data.objects.get('kasumi_body')
rig = bpy.data.objects.get('Kasumi_rig')

# Check armature modifier
arm_mod = body.modifiers.get('rig')
print("Armature modifier on body:")
print("  name:", arm_mod.name)
print("  type:", arm_mod.type)
print("  show_viewport:", arm_mod.show_viewport)
print("  object:", arm_mod.object)
print("  vertex_group:", repr(arm_mod.vertex_group))

# Check Kasumi_rig pose mode
print("Rig mode:", rig.mode)
print("Rig data pose_position:", rig.data.pose_position) # 'POSE' or 'REST'?!
# WAIT! What if rig.data.pose_position is 'REST'?!
