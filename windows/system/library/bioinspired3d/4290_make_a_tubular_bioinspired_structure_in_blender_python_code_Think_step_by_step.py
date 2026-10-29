# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_tubular_bioinspired_structure_in_blender_python_code_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a tubular bioinspired structure in blender python code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the creation of the tubular structure
count_of_tubules = 20
ellipse_stretch = 1.8
radius_of_each_tubule = 0.09

# Function to create a cube with tubules
def construct_tubule_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count_of_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    # Calculate positions for tubules
    for i in range(count_of_tubules):
        x = offset + (i % grid_dim) * spacing
        y = offset + (i // grid_dim) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_each_tubule, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipse_stretch

        # Add Boolean modifier to subtract tubule from cube
        bool_mod = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
construct_tubule_cube()
