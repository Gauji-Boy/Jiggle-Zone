import bpy

body = bpy.data.objects.get('kasumi_body')
for s in [set(), {'OBJECT'}, {'DATA'}, {'TIME'}]:
    try:
        body.update_tag(refresh=s)
        print("Success with refresh =", s)
    except Exception as e:
        print("Failed with refresh =", s, ":", e)
