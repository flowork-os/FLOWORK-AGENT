# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script_generate_a_tubular_porous_bioinspired_material_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script generate a tubular porous bioinspired material think step by step.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubules
tubule_count = 25

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        return bpy.context.object

    def calculate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(self.count)]

    def create_tubules(self):
        cube = self.create_cube()
        positions = self.calculate_positions()
        
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubules
creator = TubuleCreator(tubule_count)
creator.create_tubules()
