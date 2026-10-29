# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_blender_python_code_that_makes_a_model_of_elliptical_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create blender python code that makes a model of elliptical cylinder.

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

# Create vertices and faces for the elliptical cylinder
verts = []
faces = []

# Create the top and bottom circles
for i in range(segments):
    angle = (i / segments) * 2 * math.pi
    x = radius_x * math.cos(angle)
    y = radius_y * math.sin(angle)
    verts.append((x, y, height / 2))  # Top circle
    verts.append((x, y, -height / 2)) # Bottom circle

# Create faces
for i in range(segments):
    next_i = (i + 1) % segments
    # Top face
    faces.append((i * 2, next_i * 2, next_i * 2 + 1, i * 2 + 1))

# Add the vertices and faces to the mesh
mesh.from_pydata(verts, [], faces)
mesh.update()

# Set the object as active and select it
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
