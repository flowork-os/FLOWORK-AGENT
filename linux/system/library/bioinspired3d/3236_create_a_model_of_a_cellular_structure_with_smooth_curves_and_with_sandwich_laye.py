# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_cellular_structure_with_smooth_curves_and_with_sandwich_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a cellular structure with smooth curves and with sandwich layers using a Blender code

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular sandwich
strut_thickness = 0.2  # Thickness of the struts
smoothness = 3  # Level of smoothness
sandwich_thickness = 0.1  # Thickness of the top and bottom sandwich slabs


def build_cellular_sandwich():
    # Function to create a cellular sandwich structure
    # 1. Start with a cube.
    # 2. Fracture the cube into smaller pieces.
    # 3. Create a wireframe structure.
    # 4. Smooth the edges with a subdivision surface.
    # 5. Add top and bottom slabs.

    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object

    # Scale the cube
    base_cube.scale = (1, 1, 0.75)
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
    if base_cube and base_cube.name in bpy.data.objects:
        bpy.data.objects.remove(base_cube, do_unlink=True)

    # Join fractured pieces
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

    # Clean up geometry
    active_mesh = bpy.context.view_layer.objects.active
    if active_mesh and active_mesh.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Apply Subsurface Modifier
        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothness
        subsurf_mod.render_levels = smoothness

    # Define slab heights
    wireframe_height = 1.5  # Height of the object
    bottom_slab_position = -wireframe_height / 2 - sandwich_thickness / 2
    top_slab_position = wireframe_height / 2 + sandwich_thickness / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, sandwich_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, sandwich_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)


# Build the cellular sandwich structure
build_cellular_sandwich()
