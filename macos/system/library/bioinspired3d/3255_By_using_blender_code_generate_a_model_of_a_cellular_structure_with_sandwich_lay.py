# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code_generate_a_model_of_a_cellular_structure_with_sandwich_lay" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code generate a model of a cellular structure with sandwich layers and with smooth curves.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.2  # Thickness of the struts
smooth_factor = 6      # Level of smoothness
sandwich_height = 0.4   # Height of the sandwich slabs


def build_sandwich_structure():
    # This function creates a smooth cellular sandwich structure.
    # Steps:
    # 1. Create a cube.
    # 2. Fracture the cube.
    # 3. Merge fragments.
    # 4. Apply wireframe and subsurface modifiers.
    # 5. Add slabs on top and bottom.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    # Scale the cube
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube
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
    if cube and cube.name in bpy.data.objects:
        bpy.data.objects.remove(cube, do_unlink=True)

    # Select and join fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    first_object = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_object is None:
                first_object = obj
    if first_object:
        bpy.context.view_layer.objects.active = first_object
        bpy.ops.object.join()

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.type == 'MESH':
        active_object = bpy.context.view_layer.objects.active
        # Clean the mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe Modifier
        wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_thickness
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Add Subsurface Modifier
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_factor
        subsurf_modifier.render_levels = smooth_factor

    # Calculate positions for slabs
    wireframe_height = 1.5
    bottom_slab_position = -wireframe_height / 2 - sandwich_height / 2
    top_slab_position = wireframe_height / 2 + sandwich_height / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, sandwich_height / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, sandwich_height / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to build the sandwich structure
build_sandwich_structure()
