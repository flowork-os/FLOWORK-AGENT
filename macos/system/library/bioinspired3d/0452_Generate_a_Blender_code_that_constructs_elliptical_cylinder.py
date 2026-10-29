# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_constructs_elliptical_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that constructs elliptical cylinder.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the elliptical cylinder
radius_x = 1.0  # Radius along the X-axis
radius_y = 0.5  # Radius along the Y-axis
height = 2.0    # Height of the cylinder
segments = 32   # Number of segments for the ellipse

# Create a new mesh and object
mesh = bpy.data.meshes.new("EllipticalCylinder")
obj = bpy.data.objects.new("EllipticalCylinder", mesh)

# Link the object to the scene
bpy.context.collection.objects.link(obj)

# Create vertices for the elliptical base
verts = []
for i in range(segments):
    angle = (i / segments) * 2 * math.pi
    x = radius_x * math.cos(angle)
    y = radius_y * math.sin(angle)
    verts.append((x, y, 0))  # Base vertices at z=0
    verts.append((x, y, height))  # Top vertices at z=height

# Create faces for the sides of the cylinder
faces = []
for i in range(segments):
    next_i = (i + 1) % segments
    # Two triangles for each rectangle side
    faces.append((i * 2, next_i * 2, next_i * 2 + 1))
    faces.append((i * 2, next_i * 2 + 1, i * 2 + 1))

# Create the mesh from the vertices and faces
mesh.from_pydata(verts, [], faces)
mesh.update()

# Set the object to be the active object
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
