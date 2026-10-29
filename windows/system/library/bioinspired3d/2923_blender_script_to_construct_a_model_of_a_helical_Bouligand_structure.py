# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_construct_a_model_of_a_helical_Bouligand_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to construct a model of a helical Bouligand structure.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
num_layers = 8  # Total layers
rotation_angle = 10  # Degrees of rotation per layer

# Layer creation function

def create_helical_layer(i):
    total_height = 2
    cube_size = 2
    thickness = total_height / num_layers

    # Calculate the Z position for the layer
    z_pos = i * thickness

    # Create a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_pos))
    layer_object = bpy.context.object

    # Scale to create a thin layer
    layer_object.scale[2] = thickness / 2

    # Make the object active and selected
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    # Rotate the layer around Z-axis
    bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

# Build the helical structure
for i in range(num_layers):
    create_helical_layer(i)
