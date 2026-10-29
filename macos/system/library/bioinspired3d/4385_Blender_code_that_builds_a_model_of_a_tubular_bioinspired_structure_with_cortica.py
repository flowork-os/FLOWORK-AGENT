# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_builds_a_model_of_a_tubular_bioinspired_structure_with_cortica" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that builds a model of a tubular bioinspired structure with cortical layers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular assembly
tubule_count = 25  # Number of tubules in the assembly
layer_thickness = 0.03  # Thickness of the surrounding layer

class TubularAssembly:
    def __init__(self, tubule_count, layer_thickness):
        self.tubule_count = tubule_count
        self.layer_thickness = layer_thickness

    def create_structure(self):
        # Create the main cube
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        main_cube = bpy.context.object

        # Calculate grid dimensions
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        # Generate positions for tubules
        positions = [(offset + (i % grid_size) * spacing,
                      offset + (i // grid_size) * spacing)
                     for i in range(self.tubule_count)]

        created_tubules = []

        for x, y in positions:
            # Create inner and outer tubules
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
            inner_tubule = bpy.context.object

            bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.layer_thickness, depth=2, location=(x, y, 0))
            outer_tubule = bpy.context.object

            # Apply Boolean modifier to subtract inner from cube
            bool_mod = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = inner_tubule
            bpy.context.view_layer.objects.active = main_cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)

            # Apply Boolean modifier to create shell around inner tubule
            shell_mod = inner_tubule.modifiers.new(name=f"Shell_{x}_{y}", type='BOOLEAN')
            shell_mod.operation = 'DIFFERENCE'
            shell_mod.object = outer_tubule
            bpy.context.view_layer.objects.active = inner_tubule
            bpy.ops.object.modifier_apply(modifier=shell_mod.name)

            # Remove outer tubule
            bpy.data.objects.remove(outer_tubule, do_unlink=True)

            created_tubules.append(inner_tubule)

        # Join all tubules into one object
        if created_tubules:
            bpy.ops.object.select_all(action='DESELECT')
            for tubule in created_tubules:
                tubule.select_set(True)
            bpy.context.view_layer.objects.active = created_tubules[0]
            bpy.ops.object.join()
            final_tubular_structure = bpy.context.object
            final_tubular_structure.name = "Final_Tubular_Structure"

# Instantiate and create the tubular assembly
assembly = TubularAssembly(tubule_count, layer_thickness)
assembly.create_structure()
