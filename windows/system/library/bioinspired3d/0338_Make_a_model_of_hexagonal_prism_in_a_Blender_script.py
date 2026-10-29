# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_hexagonal_prism_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of hexagonal prism in a Blender script

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a new mesh and a new object
mesh = bpy.data.meshes.new("HexagonalPrism")
obj = bpy.data.objects.new("HexagonalPrism", mesh)

# Link the object to the scene
bpy.context.collection.objects.link(obj)

# Define the vertices and faces for a hexagonal prism
verts = [
    (1, 0, 0), (0.5, 0.866, 0), (-0.5, 0.866, 0), (-1, 0, 0), 
    (-0.5, -0.866, 0), (0.5, -0.866, 0),  # Bottom vertices
    (1, 0, 2), (0.5, 0.866, 2), (-0.5, 0.866, 2), (-1, 0, 2), 
    (-0.5, -0.866, 2), (0.5, -0.866, 2)   # Top vertices
]

faces = [
    (0, 1, 2, 3, 4, 5),  # Bottom face
    (6, 7, 8, 9, 10, 11),  # Top face
    (0, 1, 7, 6),  # Side faces
    (1, 2, 8, 7),
    (2, 3, 9, 8),
    (3, 4, 10, 9),
    (4, 5, 11, 10),
    (5, 0, 6, 11)
]

# Create the mesh from the vertices and faces
mesh.from_pydata(verts, [], faces)
mesh.update()

# Set the object as the active object
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
