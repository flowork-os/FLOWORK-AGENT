# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_makes_a_cellular_structure_smoothed_and_with_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that makes a cellular structure smoothed and with layers on top and bottom.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich
thickness_param = 0.3
smooth_param = 1
size_param = 0.05


def construct_cellular_sandwich():
    # Function to construct a cellular sandwich structure
    # Steps to follow:
    # 1. Create a cube.
    # 2. Fracture the cube into smaller pieces.
    # 3. Create a wireframe structure.
    # 4. Smooth the edges.
    # 5. Add top and bottom slabs.

    # Enable Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Add a cube
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

    # Join fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    first_mesh = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_mesh is None:
                first_mesh = obj
    if first_mesh:
        bpy.context.view_layer.objects.active = first_mesh
        bpy.ops.object.join()

    # Clean up geometry
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
        wireframe_modifier.thickness = thickness_param
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Add Subsurface Modifier
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_param
        subsurf_modifier.render_levels = smooth_param

    # Define slab positions
    wireframe_height = 1.5
    bottom_position = -wireframe_height / 2 - size_param / 2
    top_position = wireframe_height / 2 + size_param / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, size_param / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, size_param / 2)
    bpy.ops.object.transform_apply(scale=True)


# Execute the construction of the sandwich
construct_cellular_sandwich()
