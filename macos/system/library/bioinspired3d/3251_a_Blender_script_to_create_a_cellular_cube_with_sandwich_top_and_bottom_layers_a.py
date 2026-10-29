# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_create_a_cellular_cube_with_sandwich_top_and_bottom_layers_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to create a cellular cube with sandwich top and bottom layers and with smooth curves.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular sandwich structure
strut_thickness = 0.2  # Thickness of the struts
smoothness_level = 3    # Level of smoothness
sandwich_thickness = 0.1 # Thickness of the top and bottom sandwich slabs


def generate_cellular_sandwich():
    # Function to create a smooth cellular sandwich structure.
    # Steps:
    # 1. Create a base cube.
    # 2. Fracture the cube into smaller parts.
    # 3. Merge the pieces.
    # 4. Apply wireframe and subsurface modifiers.
    # 5. Add top and bottom slabs to complete the sandwich.

    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object

    # Scale the cube
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube into fragments
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

    # Select and join fractured pieces
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

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.type == 'MESH':
        active_mesh = bpy.context.view_layer.objects.active
        # Clean up mesh geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Create Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Add Subsurface Modifier
        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothness_level
        subsurf_mod.render_levels = smoothness_level

    # Calculate positions for slabs
    height_of_wireframe = 1.5
    bottom_slab_position = -height_of_wireframe / 2 - sandwich_thickness / 2
    top_slab_position = height_of_wireframe / 2 + sandwich_thickness / 2

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

# Execute the sandwich generation function
generate_cellular_sandwich()
