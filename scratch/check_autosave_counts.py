import bpy

autosave_path = r"C:\Users\susha\AppData\Local\Temp\netosiskasumi_2_28620_autosave.blend"
# We are running inside the file when opened via -b
body = bpy.data.objects.get('kasumi_body')
print(f"Autosave file body vertex count: {len(body.data.vertices)}, face count: {len(body.data.polygons)}")
import bmesh
bm = bmesh.new()
bm.from_mesh(body.data)
multi = [e for e in bm.edges if len(e.link_faces) > 2]
print(f"Autosave file multi-edges: {len(multi)}")
bm.free()
