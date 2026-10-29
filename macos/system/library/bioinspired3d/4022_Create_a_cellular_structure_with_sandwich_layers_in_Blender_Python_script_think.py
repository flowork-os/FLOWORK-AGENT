# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_cellular_structure_with_sandwich_layers_in_Blender_Python_script_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a cellular structure with sandwich layers in Blender Python script think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the parameters for the sandwich
width_of_struts = 0.15  # Thickness of the struts
plate_thickness = 0.25  # Thickness of the top and bottom slabs

def construct_sandwich():
    # Function to build a cellular sandwich structure
    addon_utils.enable('object_fracture_cell')

    # Generate a base cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_base = bpy.context.active_object

    # Adjust the cube's scale
    cube_base.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

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

    # Clean up the original cube
    if cube_base and cube_base.name in bpy.data.objects:
        bpy.data.objects.remove(cube_base, do_unlink=True)

    # Select fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    first_mesh_object = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_mesh_object is None:
                first_mesh_object = obj
    if first_mesh_object:
        bpy.context.view_layer.objects.active = first_mesh_object
        bpy.ops.object.join()

    # Clean the geometry
    if bpy.context.selected_objects:
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = width_of_struts
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Slab height definitions
    slab_height = 1.5
    bottom_slab_z_position = -slab_height / 2 - plate_thickness / 2
    top_slab_z_position = slab_height / 2 + plate_thickness / 2

    # Create the bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, plate_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create the top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, plate_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Build the sandwich structure
construct_sandwich()
