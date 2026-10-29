# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_python_code_that_builds_a_cellular_material_with_layers_on_top_and" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender python code that builds a cellular material with layers on top and bottom and with smooth curves.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the sandwich structure
strut_width = 0.25  # Width of the struts
smoothness_level = 4  # Smoothness level
slab_thickness = 0.3  # Thickness of the top and bottom slabs


def generate_sandwich():
    # Function to generate a smooth cellular sandwich.
    # Steps:
    # 1. Create a base cube.
    # 2. Fracture the cube into smaller pieces.
    # 3. Apply wireframe modifier for structure.
    # 4. Use subsurface modifier for smoothing.
    # 5. Add slabs on top and bottom.

    # Activate Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create base cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    # Resize the cube
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

    # Join fractured parts into one object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()

    # Clean the geometry
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Wireframe Modifier
    wireframe_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = strut_width
    wireframe_mod.offset = -1
    wireframe_mod.use_even_offset = False
    wireframe_mod.use_relative_offset = True
    wireframe_mod.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Subsurface Modifier
    subsurf_mod = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_mod.levels = smoothness_level
    subsurf_mod.render_levels = smoothness_level

    # Create slabs
    slab_height = 1.5  # Height of the sandwich
    bottom_slab_pos = -slab_height / 2 - slab_thickness / 2
    top_slab_pos = slab_height / 2 + slab_thickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_pos))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_pos))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Call the function to generate the sandwich
generate_sandwich()
