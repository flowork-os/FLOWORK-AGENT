# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_code_that_makes_a_model_of_a_helical_Bouligand_material_with_cyli" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender code that makes a model of a helical Bouligand material with cylindrical rods forming each layer

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
num_layers = 7  # Number of layers in the helical structure
angle_increment = 15  # Angle increment for each layer
fiber_form = 'cylinder'  # Fiber shape type

# Overall dimensions
total_height = 2.0  # Complete height of the structure
plate_dimension = 2.0  # Width and length of each square plate
layer_height = total_height / num_layers  # Height of each layer

def add_fiber_shape(shape_type, diameter, x_pos, y_pos, z_pos):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

class HelicalStructure:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle

    def create_layer(self, index):
        z_pos = index * layer_height
        rotation_angle = index * self.angle

        # Create an empty object for the layer
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
        layer_empty = bpy.context.object

        fiber_diameter = layer_height
        count_of_fibers = max(1, int(plate_dimension / fiber_diameter))

        total_space = count_of_fibers * fiber_diameter
        extra_space = plate_dimension - total_space
        start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (extra_space / 2)

        for i in range(count_of_fibers):
            fiber_y = start_y + i * fiber_diameter
            fiber_instance = add_fiber_shape(
                shape_type=fiber_form,
                diameter=fiber_diameter,
                x_pos=0,
                y_pos=fiber_y,
                z_pos=z_pos
            )
            fiber_instance.parent = layer_empty
            fiber_instance.location = (0, fiber_y, 0)

        # Rotate the layer empty object
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer_empty
        layer_empty.select_set(True)

        bpy.ops.transform.rotate(
            value=math.radians(rotation_angle),
            orient_axis='Z'
        )

        return layer_empty

# Instantiate and build the helical structure
structure = HelicalStructure(num_layers, angle_increment)
for index in range(structure.layers):
    structure.create_layer(index)
