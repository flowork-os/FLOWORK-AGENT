# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_makes_a_helical_Bouligand_bioinspired_material_made_of_cylin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that makes a helical Bouligand bioinspired material made of cylindrical fibers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 7
rotation_angle = 15
fiber_shape = 'cylinder'

total_height = 2
plate_dimensions = 2
layer_height = total_height / num_layers

def generate_fiber(shape, diameter, location):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimensions,
            location=location,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

class HelicalStructure:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle

    def create_layer(self, index):
        z_pos = index * layer_height
        rotation = index * self.angle

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
        parent_empty = bpy.context.object

        fiber_diameter = layer_height
        fibers_count = max(1, int(plate_dimensions / fiber_diameter))

        total_fiber_space = fibers_count * fiber_diameter
        remaining_space = plate_dimensions - total_fiber_space
        start_y = -plate_dimensions / 2 + (fiber_diameter / 2) + (remaining_space / 2)

        for i in range(fibers_count):
            fiber_y = start_y + i * fiber_diameter
            fiber = generate_fiber(fiber_shape, fiber_diameter, (0, fiber_y, z_pos))
            fiber.parent = parent_empty
            fiber.location = (0, fiber_y, 0)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = parent_empty
        parent_empty.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helical_structure = HelicalStructure(num_layers, rotation_angle)
helical_structure.build()
