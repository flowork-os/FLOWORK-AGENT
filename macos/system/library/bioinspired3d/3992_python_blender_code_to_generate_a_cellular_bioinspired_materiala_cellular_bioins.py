# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_generate_a_cellular_bioinspired_materiala_cellular_bioins" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to generate a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with layers on top and bottom. Think step by step.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the sandwich structure
thickness = 0.1
size = 0.4

def create_cellular_sandwich(thickness, size):
    # Function to create a sandwich with a cellular structure
    addon_utils.enable('object_fracture_cell')

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    # Scale the cube
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube into pieces
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
    if cube:
        bpy.data.objects.remove(cube, do_unlink=True)

    # Join all parts together
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.object.join()

    # Clean the geometry
    active_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply Wireframe Modifier
    wireframe = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe.thickness = thickness
    wireframe.offset = -1
    wireframe.use_even_offset = False
    wireframe.use_relative_offset = True
    wireframe.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Calculate positions for the slabs
    slab_height = 1.5
    bottom_slab_z = -slab_height / 2 - size / 2
    top_slab_z = slab_height / 2 + size / 2

    # Create slabs
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, size / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, size / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the sandwich creation
create_cellular_sandwich(thickness, size)
