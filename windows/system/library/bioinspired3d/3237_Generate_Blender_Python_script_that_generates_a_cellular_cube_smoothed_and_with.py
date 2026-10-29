# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_generates_a_cellular_cube_smoothed_and_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that generates a cellular cube smoothed and with sandwich layers

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_width = 0.25  # Width of struts
smoothness_level = 4  # Smoothing level
slab_thickness = 0.3  # Thickness for the slabs


def generate_sandwich():
    # This function creates a smooth cellular sandwich.
    # Steps:
    # 1. Create a cube.
    # 2. Fracture the cube.
    # 3. Create a wireframe.
    # 4. Add a subdivision surface for smoothing.
    # 5. Add top and bottom slabs.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Add a cube mesh
    bpy.ops.mesh.primitive_cube_add()
    cube_mesh = bpy.context.active_object

    # Adjust the cube's scale
    cube_mesh.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Execute the fracture operation
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
        use_remove_original=True,
        collection_name='',
        use_debug_points=False,
        use_debug_redraw=True,
        use_debug_bool=False
    )

    # Remove the original cube
    if cube_mesh and cube_mesh.name in bpy.data.objects:
        bpy.data.objects.remove(cube_mesh, do_unlink=True)

    # Combine fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    first_piece = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_piece is None:
                first_piece = obj
    if first_piece:
        bpy.context.view_layer.objects.active = first_piece
        bpy.ops.object.join()

    # Clean the geometry
    active_object = bpy.context.view_layer.objects.active
    if active_object and active_object.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe Modifier
        wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_width
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Add Subsurface Modifier
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smoothness_level
        subsurf_modifier.render_levels = smoothness_level

    # Define positions for slabs
    wireframe_height = 1.5
    bottom_position = -wireframe_height / 2 - slab_thickness / 2
    top_position = wireframe_height / 2 + slab_thickness / 2

    # Create the bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create the top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)


# Execute the sandwich generation
generate_sandwich()
