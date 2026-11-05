import bpy
import bmesh

body = bpy.data.objects.get('kasumi_body')
bm = bmesh.new()
bm.from_mesh(body.data)

non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
more_than_two = [e for e in bm.edges if len(e.link_faces) > 2]
print(f"Total non-manifold edges: {len(non_manifold_edges)}")
print(f"Edges with > 2 polygons: {len(more_than_two)}")

for e in more_than_two[:5]:
    print(f"  Edge {e.index}: verts {[v.index for v in e.verts]}, link_faces: {len(e.link_faces)}")

bm.free()
