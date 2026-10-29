# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code__create_cube_with_small_spheres_subtracted_from_each_f" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code, create cube with small spheres subtracted from each face center.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object

# Create small spheres and subtract them from the cube
sphere_radius = 0.2
for i in range(6):
    # Calculate the position for each face center
    if i == 0:  # Front face
        location = (0, 1, 0)
    elif i == 1:  # Back face
        location = (0, -1, 0)
    elif i == 2:  # Top face
        location = (0, 0, 1)
    elif i == 3:  # Bottom face
        location = (0, 0, -1)
    elif i == 4:  # Right face
        location = (1, 0, 0)
    elif i == 5:  # Left face
        location = (-1, 0, 0)

    # Create a small sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=sphere_radius, location=location)
    sphere = bpy.context.object

    # Select the sphere and the cube
    bpy.ops.object.select_all(action='DESELECT')
    cube.select_set(True)
    sphere.select_set(True)
    
    # Set the active object to the cube
    bpy.context.view_layer.objects.active = cube
    
    # Perform the boolean operation
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["Boolean"].object = sphere
    bpy.ops.object.modifier_apply(modifier="Boolean")
    
    # Delete the sphere
    bpy.data.objects.remove(sphere)

# Optionally, select the cube to see the result
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
