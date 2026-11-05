import bpy

print("=== ALL OBJECTS IN SCENE ===")
for obj in bpy.context.scene.objects:
    print(f"Name: {obj.name}, type: {obj.type}, hide_viewport: {obj.hide_viewport}, hide_get: {obj.hide_get()}, location: {obj.location}")
