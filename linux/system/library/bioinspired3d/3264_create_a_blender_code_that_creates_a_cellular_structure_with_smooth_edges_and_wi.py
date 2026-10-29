# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_blender_code_that_creates_a_cellular_structure_with_smooth_edges_and_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a blender code that creates a cellular structure with smooth edges and with sandwich layers

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters
cell_thickness = 0.1
smooth_level = 4
sandwich_height = 0.3

# Function to create the sandwich structure

def make_cellular_sandwich():
    # Enable necessary add-on
    addon_utils.enable('object_fracture_cell')
    
    # Create initial cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = (1, 1, 0.75)
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
    
    # Delete the original cube
    bpy.data.objects.remove(cube, do_unlink=True)
    
    # Join fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    
    # Clean geometry
    active_mesh = bpy.context.view_layer.objects.active
    if active_mesh and active_mesh.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Add Wireframe Modifier
        wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = cell_thickness
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')
        
        # Add Subsurface Modifier
        subsurf_modifier = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_level
        subsurf_modifier.render_levels = smooth_level
    
    # Define slab heights
    slab_height = 1.5
    bottom_slab_z = -slab_height / 2 - sandwich_height / 2
    top_slab_z = slab_height / 2 + sandwich_height / 2
    
    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, sandwich_height / 2)
    bpy.ops.object.transform_apply(scale=True)
    
    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, sandwich_height / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the creation of the sandwich
make_cellular_sandwich()
