import bpy

body = bpy.data.objects.get('kasumi_body')
print("update_tag doc:", bpy.types.Object.update_tag.__doc__)

# Test calling update_tag()
body.update_tag(refresh={'OBJECT', 'DATA'})
print("update_tag success!")
