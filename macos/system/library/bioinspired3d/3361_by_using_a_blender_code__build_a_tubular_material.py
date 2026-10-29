# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code__build_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code, build a tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubules to create
number_of_tubules = 14  # Total tubules

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def build_structure(self):
        # Create the base cube and subtract tubules from it.
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start = -1 + spacing / 2
        
        positions = [(start + (i % grid_size) * spacing,
                       start + (i // grid_size) * spacing)
                      for i in range(self.count)]
        
        for pos_x, pos_y in positions:
            self.create_and_subtract_tubule(cube, pos_x, pos_y)

    def create_and_subtract_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_modifier = cube.modifiers.new(name=f"Cutout_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the tubular structure
creator = TubuleCreator(number_of_tubules)
creator.build_structure()
