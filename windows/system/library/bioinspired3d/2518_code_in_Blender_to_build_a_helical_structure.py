# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_build_a_helical_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to build a helical structure

import bpy
import math

# Remove all existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical parameters
layer_count = 9  # Total layers in the helical structure
rotation_increment = 12  # Degrees per layer

# Function to create a helical layer
def create_helical_layer(idx):
    total_height = 2  # Complete height
    plate_dimension = 2  # Plate dimension
    individual_thickness = total_height / layer_count  # Calculate individual thickness

    # Calculate the height for the current layer
    current_height = idx * individual_thickness

    # Add a cube for the layer
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, current_height))
    layer_object = bpy.context.object

    # Scale the layer to create a thin plate
    layer_object.scale[2] = individual_thickness / 2

    # Make the layer the active object
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(idx * rotation_increment), orient_axis='Z')

# Build the helical structure
for i in range(layer_count):
    create_helical_layer(i)
