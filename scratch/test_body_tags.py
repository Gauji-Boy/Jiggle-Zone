import bpy

body = bpy.data.objects.get('kasumi_body')
print("Has update_tag on body?", hasattr(body, 'update_tag'))
for m in dir(body):
    if 'tag' in m or 'update' in m:
        print(f"  body.{m}")
