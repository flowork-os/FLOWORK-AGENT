# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_python_blender_code__build_a_model_of_a_cellular_structure_with_smooth_cur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using python blender code, build a model of a cellular structure with smooth curves Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular structure
strut_thickness = 0.2  # Thickness of the struts
smoothness_level = 3    # Level of smoothness

def generate_cellular_structure():
    # Function to create a smooth cellular model.
    # Steps:
    # 1. Add a cube.
    # 2. Fracture the cube and merge fragments.
    # 3. Use wireframe modifier for cellular design.
    # 4. Apply subsurface modifier for smoothing.

    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    base_cube = bpy.context.object
    
    # Fracture the cube into smaller pieces
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

    # Remove the original cube after fracturing
    if base_cube and base_cube.name in bpy.data.objects:
        bpy.data.objects.remove(base_cube, do_unlink=True)
    
    # Select fractured pieces
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
    
    # Clean up the geometry
    if bpy.context.selected_objects and bpy.context.view_layer.objects.active:
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Wireframe Modifier for cellular structure
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True

        # Subsurface Modifier for smoothing
        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothness_level
        subsurf_mod.render_levels = smoothness_level

# Execute the function to create the structure
generate_cellular_structure()
