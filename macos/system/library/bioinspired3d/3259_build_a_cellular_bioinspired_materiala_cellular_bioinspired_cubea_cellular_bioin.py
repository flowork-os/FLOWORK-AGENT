# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_cellular_bioinspired_materiala_cellular_bioinspired_cubea_cellular_bioin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with layers on top and bottom and with smooth edges in a Blender script

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Variables for the cellular sandwich parameters
strut_width = 0.3  # Width of the struts
subdivision_level = 2  # Level of smoothness
slab_thickness = 0.4  # Thickness of the top and bottom sandwich slabs


def construct_cellular_sandwich():
    # Function to construct a smooth cellular sandwich.
    # Steps:
    # 1. Create a cube as a base object.
    # 2. Fracture the cube into smaller pieces.
    # 3. Apply wireframe modifier for cellular look.
    # 4. Use subsurface modifier for smooth edges.
    # 5. Add top and bottom slabs to complete the structure.

    # Enable Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add()
    initial_cube = bpy.context.active_object

    # Scale the cube
    initial_cube.scale = (1, 1, 0.75)
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
    if initial_cube and initial_cube.name in bpy.data.objects:
        bpy.data.objects.remove(initial_cube, do_unlink=True)

    # Join the fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()

    # Clean up geometry
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Wireframe Modifier
    wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_modifier.thickness = strut_width
    wireframe_modifier.offset = -1
    wireframe_modifier.use_even_offset = False
    wireframe_modifier.use_relative_offset = True
    wireframe_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Subsurface Modifier
    subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_modifier.levels = subdivision_level
    subsurf_modifier.render_levels = subdivision_level

    # Create slabs
    sandwich_height = 1.5  # Height of the sandwich
    bottom_slab_position = -sandwich_height / 2 - slab_thickness / 2
    top_slab_position = sandwich_height / 2 + slab_thickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to construct the sandwich
construct_cellular_sandwich()
