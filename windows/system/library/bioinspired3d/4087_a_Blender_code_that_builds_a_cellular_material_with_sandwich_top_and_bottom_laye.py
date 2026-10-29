# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_builds_a_cellular_material_with_sandwich_top_and_bottom_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that builds a cellular material with sandwich top and bottom layers and with smooth edges. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
cell_thickness = 0.25
smooth_factor = 5
total_size = 0.1

# Main function to build the sandwich
def build_cellular_sandwich():
    # Enable the required add-on
    addon_utils.enable('object_fracture_cell')
    
    # Add a cube to serve as the base
    bpy.ops.mesh.primitive_cube_add()
    starting_cube = bpy.context.active_object
    starting_cube.scale = (1, 1, 0.75)
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
    bpy.data.objects.remove(starting_cube, do_unlink=True)
    
    # Join all fractured pieces
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
    
    # Clean geometry
    active_object = bpy.context.view_layer.objects.active
    if active_object and active_object.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create Wireframe Modifier
        wireframe_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = cell_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')
        
        # Create Subsurface Modifier
        subsurf_mod = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smooth_factor
        subsurf_mod.render_levels = smooth_factor
    
    # Define slab heights
    slab_height = 1.5
    bottom_slab_position = -slab_height / 2 - total_size / 2
    top_slab_position = slab_height / 2 + total_size / 2
    
    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, total_size / 2)
    bpy.ops.object.transform_apply(scale=True)
    
    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, total_size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Run the function to create the sandwich
build_cellular_sandwich()
