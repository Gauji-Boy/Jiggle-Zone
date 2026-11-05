import bpy

path = r"E:\3D models\modles\Netosis_-_Kasumi\netosiskasumi_2.blend"
body = bpy.data.objects.get('kasumi_body')
print(f"Original file body vertex count: {len(body.data.vertices)}, face count: {len(body.data.polygons)}")

autosave_path = r"C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_28620_autosave.blend"
# Check autosave
import bmesh
bm = bmesh.new()
bm.from_mesh(body.data)
multi = [e for e in bm.edges if len(e.link_faces) > 2]
print(f"Original file multi-edges: {len(multi)}")
bm.free()
