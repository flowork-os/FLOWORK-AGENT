# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_generating_a_model_of_a_cellular_bioinspired_materiala_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for generating a model of a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with sandwich layers Think step by step

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specifications for the sandwich structure
strut_size = 0.3  # Thickness of the struts
slab_size = 0.05   # Thickness of the top and bottom slabs

def cellular_structure():
    # Function to create a cellular sandwich structure.
    # Activate Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Perform the fracture operation
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
    bpy.data.objects.remove(base_cube, do_unlink=True)

    # Select and join all fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.join()
            break

    # Clean up geometry
    if bpy.context.selected_objects and bpy.context.view_layer.objects.active:
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Create Wireframe Modifier
        wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_size
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Define positions for the slabs
    sandwich_height = 1.5
    bottom_slab_position = -sandwich_height / 2 - slab_size / 2
    top_slab_position = sandwich_height / 2 + slab_size / 2

    # Create the bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create the top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Create the cellular sandwich
cellular_structure()
