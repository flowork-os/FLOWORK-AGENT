# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_generate_a_cellular_cube_with_sandwich_top_and_bottom_layers_and" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to generate a cellular cube with sandwich top and bottom layers and with smooth curves Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.2
smoothness_level = 3
slab_size = 0.1

# Function to build the sandwich structure
def construct_cellular_sandwich():
    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create initial cube
    bpy.ops.mesh.primitive_cube_add()
    initial_cube = bpy.context.active_object
    initial_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

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
    bpy.data.objects.remove(initial_cube, do_unlink=True)

    # Merge fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean up the geometry
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add Wireframe Modifier
    wire_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wire_mod.thickness = strut_thickness
    wire_mod.offset = -1
    wire_mod.use_even_offset = False
    wire_mod.use_relative_offset = True
    wire_mod.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Add Subsurface Modifier
    sub_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
    sub_mod.levels = smoothness_level
    sub_mod.render_levels = smoothness_level

    # Create slabs
    slab_height = 1.5
    bottom_slab_z = -slab_height / 2 - slab_size / 2
    top_slab_z = slab_height / 2 + slab_size / 2

    # Bottom slab creation
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab creation
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to create the sandwich
construct_cellular_sandwich()
