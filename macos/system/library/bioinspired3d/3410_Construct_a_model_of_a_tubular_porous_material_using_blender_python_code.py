# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_tubular_porous_material_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a tubular porous material using blender python code

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the model
count = 22
stretch = 1.6
radius = 0.08

# Function to create the tubule structure

def create_tubule_structure(count, stretch, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    interval = 2 / grid_size
    offset = -1 + interval / 2
    
    for i in range(count):
        x_pos = offset + (i % grid_size) * interval
        y_pos = offset + (i // grid_size) * interval
        
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x_pos, y_pos, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch
        
        bool_mod = cube.modifiers.new(name=f"Boolean_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Run the function to create the geometry
create_tubule_structure(count, stretch, radius)
