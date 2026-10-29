# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_make_a_model_of_a_cellular_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to make a model of a cellular cube

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Thickness of the struts
strut_thickness = 0.2

def build_cell_structure():
    # Constructs a cellular structure by fracturing a cube.
    # Steps:
    # 1. Add a cube to the scene.
    # 2. Fracture the cube into smaller segments.
    # 3. Apply the wireframe modifier to achieve the final look.

    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2)
    base_cube = bpy.context.object
    
    # Execute the Fracture Cell operation
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
    
    # Select all fractured pieces to join them
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
        # Optimize geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Add Wireframe Modifier
        wf_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = strut_thickness
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True

# Create the cellular structure
build_cell_structure()
