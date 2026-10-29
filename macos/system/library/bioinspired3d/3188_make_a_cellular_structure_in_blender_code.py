# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_cellular_structure_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a cellular structure in blender code

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Thickness of the struts in the cellular structure
strut_size = 0.3


def construct_cell_structure():
    # Function to create the cellular structure
    # Summary:
    # 1. Create a cube
    # 2. Fracture the cube
    # 3. Apply wireframe modifier

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_model = bpy.context.object
    
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
    # Remove the original cube
    if cube_model and cube_model.name in bpy.data.objects:
        bpy.data.objects.remove(cube_model, do_unlink=True)
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if mesh_objects:
        for obj in mesh_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.join()
    
    if bpy.context.selected_objects:
        active_object = bpy.context.view_layer.objects.active
        # Clean up geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Add Wireframe Modifier
        wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_size
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True

# Call the function to construct the cell structure
construct_cell_structure()
