# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_cellular_bioinspired_materiala_cellular_bioinspired_cubea_ce" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with smooth curves in Blender Python script

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular structure
cell_thickness = 0.3
smooth_level = 2

def construct_cell_structure():
    # This function constructs a cellular structure with smoothing.
    # Process:
    # 1. Create a cube.
    # 2. Fracture it into smaller pieces.
    # 3. Apply a wireframe modifier for cellular appearance.
    # 4. Smooth the result with a subsurface modifier.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube = bpy.context.object

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

    # Deselect all objects
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

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active:
        active_mesh = bpy.context.view_layer.objects.active
        # Clean up geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Wireframe Modifier
        wf_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = cell_thickness
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True

        # Subsurface Modifier
        subsurf_modifier = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_level
        subsurf_modifier.render_levels = smooth_level

# Construct the cellular structure
construct_cell_structure()
