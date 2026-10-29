# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code__build_a_cellular_structure_with_smooth_curves" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code, build a cellular structure with smooth curves.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set parameters for the structure
cell_thickness = 0.15  # Thickness of the struts
smooth_level = 4        # Level of smoothness

def create_cell_structure():
    # This function constructs a smooth cellular structure.
    # 1. Add a cube.
    # 2. Fracture the cube into pieces.
    # 3. Apply wireframe modifier for cellular effect.
    # 4. Use subsurface modifier for edge smoothing.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create an initial cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    initial_cube = bpy.context.object
    
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
    
    # Select all fractured objects
    bpy.ops.object.select_all(action='DESELECT')
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for obj in mesh_objects:
        obj.select_set(True)
    if mesh_objects:
        bpy.context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.join()
    
    # Clean the geometry
    if bpy.context.selected_objects:
        active_object = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply Wireframe Modifier
        wf_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = cell_thickness
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True

        # Apply Subsurface Modifier
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_level
        subsurf_modifier.render_levels = smooth_level

# Create the cellular structure
create_cell_structure()
