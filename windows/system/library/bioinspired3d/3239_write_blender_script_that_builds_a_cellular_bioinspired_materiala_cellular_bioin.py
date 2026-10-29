# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_script_that_builds_a_cellular_bioinspired_materiala_cellular_bioin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender script that builds a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with layers on top and bottom and with smooth curves.

import bpy
import addon_utils

# Clear the existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the sandwich structure
thickness_value = 0.1
smooth_level_value = 2
size_value = 0.4


def create_sandwich_structure():
    # Function to create a smooth cellular sandwich
    # Steps involved:
    # 1. Start with a cube.
    # 2. Fracture the cube into pieces.
    # 3. Create a wireframe structure.
    # 4. Smooth the edges.
    # 5. Add top and bottom slabs.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    # Scale the cube
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

    # Remove the original cube
    if cube and cube.name in bpy.data.objects:
        bpy.data.objects.remove(cube, do_unlink=True)

    # Join fractured pieces
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

    # Clean up geometry
    active_mesh = bpy.context.view_layer.objects.active
    if active_mesh and active_mesh.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = thickness_value
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

        # Apply Subsurface Modifier
        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smooth_level_value
        subsurf_mod.render_levels = smooth_level_value

    # Define slab positions
    wireframe_height = 1.5
    bottom_slab_position = -wireframe_height / 2 - size_value / 2
    top_slab_position = wireframe_height / 2 + size_value / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, size_value / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, size_value / 2)
    bpy.ops.object.transform_apply(scale=True)


# Create the sandwich structure
create_sandwich_structure()
