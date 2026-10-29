# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code__create_a_model_of_a_cellular_bioinspired_materiala_ce" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code, create a model of a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with sandwich layers think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular sandwich
strut_thickness = 0.2  # Thickness of the struts
sandwich_thickness = 0.3  # Thickness of the top and bottom slabs

# Function to create the sandwich structure
def build_cellular_sandwich():
    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube into smaller pieces
    bpy.ops.object.add_fracture_cell_objects(
        source={'PARTICLE_OWN'},
        source_limit=100,
        source_noise=0.5,
        cell_scale=(1, 1, 1),
        recursion=0,
        recursion_source_limit=8,
        recursion_clamp=250,
        recursion_chance=0.25,
        recursion_chance_select='SIZE_MIN',
        use_smooth_faces=False,
        use_sharp_edges=True,
        use_sharp_edges_apply=True,
        use_data_match=True,
        use_island_split=True,
        margin=0.001,
        material_index=0,
        use_interior_vgroup=False,
        mass_mode='VOLUME',
        mass=1,
        use_recenter=True,
        use_remove_original=True
    )

    # Remove the original cube
    bpy.data.objects.remove(base_cube, do_unlink=True)

    # Select and join fractured pieces
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean up geometry
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Wireframe modifier
    wf_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wf_modifier.thickness = strut_thickness
    wf_modifier.offset = -1
    wf_modifier.use_even_offset = False
    wf_modifier.use_relative_offset = True
    wf_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Create sandwich slabs
    slab_height = 1.5
    bottom_z = -slab_height / 2 - sandwich_thickness / 2
    top_z = slab_height / 2 + sandwich_thickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, sandwich_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, sandwich_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to create the structure
build_cellular_sandwich()
