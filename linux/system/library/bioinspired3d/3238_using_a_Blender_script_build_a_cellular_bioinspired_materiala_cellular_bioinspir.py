# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_build_a_cellular_bioinspired_materiala_cellular_bioinspir" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script build a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with smooth curves and with layers on top and bottom

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Constants for the cellular sandwich
strut_thickness_value = 0.15
smoothness_degree = 5
sandwich_thickness_value = 0.2


def create_cellular_structure():
    # Function to create a cellular sandwich structure
    # Steps involved:
    # 1. Create a cube.
    # 2. Fracture the cube.
    # 3. Apply wireframe.
    # 4. Smooth the edges.
    # 5. Add slabs on top and bottom.

    # Enable the fracture cell add-on
    addon_utils.enable('object_fracture_cell')

    # Add a cube mesh
    bpy.ops.mesh.primitive_cube_add()
    cube_object = bpy.context.active_object

    # Scale the cube
    cube_object.scale = (1, 1, 0.75)
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
    if cube_object and cube_object.name in bpy.data.objects:
        bpy.data.objects.remove(cube_object, do_unlink=True)

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

    # Clean geometry
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
        wireframe_modifier.thickness = strut_thickness_value
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Add Subsurface Modifier
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smoothness_degree
        subsurf_modifier.render_levels = smoothness_degree

    # Define slab positions
    wireframe_height = 1.5
    bottom_slab_position = -wireframe_height / 2 - sandwich_thickness_value / 2
    top_slab_position = wireframe_height / 2 + sandwich_thickness_value / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, sandwich_thickness_value / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, sandwich_thickness_value / 2)
    bpy.ops.object.transform_apply(scale=True)


# Call the function to create the cellular structure
create_cellular_structure()
