# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_porous_bioinspired_material_with_cortical_layers_in_a_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular porous bioinspired material with cortical layers in a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Setup for the tubular structure
num_tubules = 12  # Number of tubules to create
layer_thickness = 0.04  # Thickness of the layer around each tubule

class TubuleCreator:
    def __init__(self, count, thickness):
        self.tubule_count = count
        self.layer_thickness = thickness

    def create_tubules(self):
        # Create a cube as the base object
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing, 
                      start_offset + (i // grid_size) * spacing) 
                     for i in range(self.tubule_count)]
        
        tubule_objects = []
        
        for x, y in positions:
            # Inner tubule
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
            inner_tubule = bpy.context.object

            # Outer tubule
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.layer_thickness, depth=2, location=(x, y, 0))
            outer_tubule = bpy.context.object
            
            # Boolean modifier to subtract inner tubule from the cube
            bool_mod = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = inner_tubule
            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            
            # Boolean modifier for the hollow layer
            layer_bool = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
            layer_bool.operation = 'DIFFERENCE'
            layer_bool.object = outer_tubule
            bpy.context.view_layer.objects.active = inner_tubule
            bpy.ops.object.modifier_apply(modifier=layer_bool.name)

            # Remove outer tubule
            bpy.data.objects.remove(outer_tubule, do_unlink=True)
            tubule_objects.append(inner_tubule)
        
        # Join all inner tubules into one object
        if tubule_objects:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in tubule_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = tubule_objects[0]
            bpy.ops.object.join()
            final_tubule_shell = bpy.context.object
            final_tubule_shell.name = "Combined_Tubule_Shell"

# Create the tubular structure
creator = TubuleCreator(num_tubules, layer_thickness)
creator.create_tubules()
