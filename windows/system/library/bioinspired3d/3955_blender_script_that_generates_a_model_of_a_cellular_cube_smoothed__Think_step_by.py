# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_a_cellular_cube_smoothed__Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of a cellular cube smoothed. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the model
wire_thickness = 0.3  # Width of the struts
subdivision_level = 6  # Level of smoothness

def construct_cell_structure():
    # Activate the Fracture Cell add-on
    addon_utils.enable("object_fracture_cell")
    bpy.ops.mesh.primitive_cube_add(size=2)
    main_cube = bpy.context.object

    # Fracture the cube into smaller parts
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
        collection_name="",
        use_debug_points=False,
        use_debug_redraw=True,
        use_debug_bool=False
    )

    # Remove the original cube after fracturing
    bpy.data.objects.remove(main_cube, do_unlink=True)

    # Select and join all fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Cleanup geometry
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply Wireframe Modifier
    wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_modifier.thickness = wire_thickness
    wireframe_modifier.offset = -1
    wireframe_modifier.use_even_offset = False
    wireframe_modifier.use_relative_offset = True
    wireframe_modifier.use_replace = True

    # Apply Subdivision Modifier
    subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_modifier.levels = subdivision_level
    subsurf_modifier.render_levels = subdivision_level

# Call the function to construct the model
construct_cell_structure()
