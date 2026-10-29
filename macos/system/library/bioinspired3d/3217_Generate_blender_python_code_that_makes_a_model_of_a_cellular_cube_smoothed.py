# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_makes_a_model_of_a_cellular_cube_smoothed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that makes a model of a cellular cube smoothed.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular structure
thickness_value = 0.1  # Thickness of the struts
smooth_level_value = 5  # Level of smoothness

def smooth_cell_structure():
    # This function creates a smooth cellular model.
    # 1. Create a cube.
    # 2. Fracture the cube into pieces.
    # 3. Apply wireframe modifier for cellular design.
    # 4. Use subsurface modifier for smoothing.

    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Add a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_object = bpy.context.object
    
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
    
    # Select fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    fractured_meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for obj in fractured_meshes:
        obj.select_set(True)
    if fractured_meshes:
        bpy.context.view_layer.objects.active = fractured_meshes[0]
        bpy.ops.object.join()
    
    # Clean up the geometry
    if bpy.context.selected_objects:
        main_object = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Wireframe Modifier
        wf_modifier = main_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = thickness_value
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True

        # Subsurface Modifier
        subsurf_modifier = main_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_level_value
        subsurf_modifier.render_levels = smooth_level_value

# Create the smooth cellular structure
smooth_cell_structure()
