# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script__construct_a_cellular_structure_with_smooth_curves_and_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script, construct a cellular structure with smooth curves and with sandwich layers

import bpy
import addon_utils

# Clear the current scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the cellular sandwich
cell_thickness = 0.1  # Thickness of struts
smoothing_factor = 5   # Level of smoothness
slab_size = 0.3       # Size of the sandwich slabs


def construct_cellular_sandwich():
    # Function to generate a smooth cellular sandwich structure.
    # Steps:
    # 1. Create a cube as a base.
    # 2. Fracture the cube into smaller fragments.
    # 3. Merge fragments.
    # 4. Add wireframe and subsurface modifiers.
    # 5. Add top and bottom slabs.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create initial cube
    bpy.ops.mesh.primitive_cube_add()
    cube_base = bpy.context.active_object

    # Adjust cube scale
    cube_base.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Apply Fracture Cell operation
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
    if cube_base and cube_base.name in bpy.data.objects:
        bpy.data.objects.remove(cube_base, do_unlink=True)

    # Select and join all fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    first_mesh_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_mesh_obj is None:
                first_mesh_obj = obj
    if first_mesh_obj:
        bpy.context.view_layer.objects.active = first_mesh_obj
        bpy.ops.object.join()

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.type == 'MESH':
        active_mesh = bpy.context.view_layer.objects.active
        # Clean mesh geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = cell_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Add Subsurface Modifier
        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothing_factor
        subsurf_mod.render_levels = smoothing_factor

    # Calculate slab positions
    wireframe_height = 1.5
    bottom_slab_position = -wireframe_height / 2 - slab_size / 2
    top_slab_position = wireframe_height / 2 + slab_size / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Call the function to construct the sandwich
construct_cellular_sandwich()
