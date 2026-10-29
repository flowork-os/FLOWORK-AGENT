# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code_create_a_cellular_cube_with_sandwich_top_and_bottom_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code create a cellular cube with sandwich top and bottom layers

import bpy
import addon_utils

# Clear the scene of all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Constants for the structure
strut_size = 0.1
slab_size = 0.4

def create_cellular_sandwich():
    # Enable the necessary add-on
    addon_utils.enable('object_fracture_cell')
    bpy.ops.mesh.primitive_cube_add()
    initial_cube = bpy.context.active_object
    initial_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracturing the cube
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
    bpy.data.objects.remove(initial_cube, do_unlink=True)

    # Select all fractured parts to join them
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    if bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
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

        # Add wireframe modifier
        wf_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = strut_size
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Create slabs for the sandwich
    bottom_slab_location = -0.75 - slab_size / 2
    top_slab_location = 0.75 + slab_size / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_location))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_location))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the sandwich creation
create_cellular_sandwich()
