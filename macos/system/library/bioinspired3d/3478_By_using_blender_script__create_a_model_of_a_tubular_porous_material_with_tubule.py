# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script__create_a_model_of_a_tubular_porous_material_with_tubule" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script, create a model of a tubular porous material with tubule layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
num_tubules = 20  # Total number of tubules
layer_thickness = 0.03  # Thickness of the layer surrounding tubules

# Class for creating the tubular structure
class TubuleCreator:
    def __init__(self, count, thickness):
        self.count = count
        self.thickness = thickness

    def build(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        
        positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(self.count)]
        layers = []
        
        for pos in positions:
            x, y = pos
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
            inner_tubule = bpy.context.object
            
            bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=2, location=(x, y, 0))
            outer_tubule = bpy.context.object
            
            self.subtract_tubule(base_cube, inner_tubule, x, y)
            self.create_hollow_layer(inner_tubule, outer_tubule, x, y)
            bpy.data.objects.remove(outer_tubule, do_unlink=True)
            layers.append(inner_tubule)
        
        self.merge_layers(layers)

    def subtract_tubule(self, cube, inner_tubule, x, y):
        modifier = cube.modifiers.new(name=f"Tubule_Bool_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    def create_hollow_layer(self, inner_tubule, outer_tubule, x, y):
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

    def merge_layers(self, layers):
        if layers:
            bpy.ops.object.select_all(action='DESELECT')
            for layer in layers:
                layer.select_set(True)
            bpy.context.view_layer.objects.active = layers[0]
            bpy.ops.object.join()
            final_shell = bpy.context.object
            final_shell.name = "Merged_Layer_Shell"

# Instantiate and build the tubular structure
creator = TubuleCreator(num_tubules, layer_thickness)
creator.build()
