# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_makes_a_model_of_a_cellular_material_with_smooth_curve" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that makes a model of a cellular material with smooth curves and with layers on top and bottom

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular sandwich structure
strut_thickness = 0.2  # Thickness of the struts
smoothness = 3  # Level of smoothness
sandwich_thickness = 0.1  # Thickness of the top and bottom sandwich slabs


def build_cellular_sandwich():
    # Function to create a smooth cellular sandwich structure.
    # Steps:
    # 1. Create a cube as base geometry.
    # 2. Fracture the cube into smaller pieces.
    # 3. Add wireframe modifier for cellular appearance.
    # 4. Apply subsurface modifier for smoothing.
    # 5. Add top and bottom slabs.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create initial cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object

    # Scale the cube to match the sandwich dimensions
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube into smaller parts
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
    if base_cube and base_cube.name in bpy.data.objects:
        bpy.data.objects.remove(base_cube, do_unlink=True)

    # Select and join fractured pieces into a single object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()

    # Clean up geometry
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add Wireframe Modifier
    wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = strut_thickness
    wireframe_mod.offset = -1
    wireframe_mod.use_even_offset = False
    wireframe_mod.use_relative_offset = True
    wireframe_mod.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Add Subsurface Modifier
    subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_mod.levels = smoothness
    subsurf_mod.render_levels = smoothness

    # Create bottom and top slabs
    slab_height = 1.5  # Height of the object to be sandwiched
    bottom_position = -slab_height / 2 - sandwich_thickness / 2
    top_position = slab_height / 2 + sandwich_thickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, sandwich_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, sandwich_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to create the sandwich structure
build_cellular_sandwich()
