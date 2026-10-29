# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code__create_a_cellular_structure_smoothed_and_with_sandwich_top" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code, create a cellular structure smoothed and with sandwich top and bottom layers.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich
strut_thickness = 0.15
smoothness_level = 6
overall_size = 0.2

# Function to create the sandwich

def construct_cellular_sandwich():
    # Enable the add-on
    addon_utils.enable('object_fracture_cell')
    
    # Create a cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    
    # Apply the Fracture Cell operation
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
    bpy.data.objects.remove(base_cube, do_unlink=True)
    
    # Join fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    
    # Clean geometry
    active_object = bpy.context.view_layer.objects.active
    if active_object and active_object.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Wireframe Modifier
        wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_thickness
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')
        
        # Subsurface Modifier
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smoothness_level
        subsurf_modifier.render_levels = smoothness_level
    
    # Define slab heights
    slab_height = 1.5
    bottom_slab_position = -slab_height / 2 - overall_size / 2
    top_slab_position = slab_height / 2 + overall_size / 2
    
    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, overall_size / 2)
    bpy.ops.object.transform_apply(scale=True)
    
    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, overall_size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the sandwich creation
construct_cellular_sandwich()
