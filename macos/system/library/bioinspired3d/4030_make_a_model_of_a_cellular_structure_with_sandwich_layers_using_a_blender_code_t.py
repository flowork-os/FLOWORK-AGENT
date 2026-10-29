# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_cellular_structure_with_sandwich_layers_using_a_blender_code_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a cellular structure with sandwich layers using a blender code think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the sandwich structure
strut_thickness = 0.3  # Thickness of the struts
slab_thickness = 0.1  # Thickness of the top and bottom slabs

def construct_cellular_sandwich():
    # Enable Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    initial_cube = bpy.context.active_object

    # Scale the cube
    initial_cube.scale = (1, 1, 0.75)
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

    # Remove the original cube
    if initial_cube and initial_cube.name in bpy.data.objects:
        bpy.data.objects.remove(initial_cube, do_unlink=True)

    # Select and join fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    first_object = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_object is None:
                first_object = obj
    if first_object:
        bpy.context.view_layer.objects.active = first_object
        bpy.ops.object.join()

    # Clean up geometry
    active_object = bpy.context.view_layer.objects.active
    if active_object and active_object.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply Wireframe Modifier
        wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_thickness
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Calculate positions for slabs
    slab_height = 1.5  # Height of the object to be sandwiched
    bottom_slab_position = -slab_height / 2 - slab_thickness / 2
    top_slab_position = slab_height / 2 + slab_thickness / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the construction function
construct_cellular_sandwich()
