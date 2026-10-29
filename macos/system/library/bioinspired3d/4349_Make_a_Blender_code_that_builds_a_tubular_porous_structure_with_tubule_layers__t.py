# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_builds_a_tubular_porous_structure_with_tubule_layers__t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that builds a tubular porous structure with tubule layers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 12  # Number of tubules in the structure
layer_thickness = 0.04  # Thickness of the layer around each tubule

class TubuleCreator:
    def __init__(self, tubule_count, thickness):
        self.tubule_count = tubule_count
        self.thickness = thickness

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        main_cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(self.tubule_count)]
        shells = []
        
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
            inner_tubule = bpy.context.object
            
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.thickness, depth=2, location=(x, y, 0))
            outer_tubule = bpy.context.object
            
            self.apply_boolean(main_cube, inner_tubule)
            self.apply_boolean(inner_tubule, outer_tubule)
            
            bpy.data.objects.remove(outer_tubule, do_unlink=True)
            shells.append(inner_tubule)
        
        self.merge_shells(shells)

    def apply_boolean(self, target, obj):
        modifier = target.modifiers.new(name=f"Bool_{obj.name}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = obj
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    def merge_shells(self, shells):
        if shells:
            bpy.ops.object.select_all(action='DESELECT')
            for shell in shells:
                shell.select_set(True)
            bpy.context.view_layer.objects.active = shells[0]
            bpy.ops.object.join()
            final_shell = bpy.context.object
            final_shell.name = "Merged_Shell"

# Create the tubular structure
creator = TubuleCreator(num_tubules, layer_thickness)
creator.create_structure()
