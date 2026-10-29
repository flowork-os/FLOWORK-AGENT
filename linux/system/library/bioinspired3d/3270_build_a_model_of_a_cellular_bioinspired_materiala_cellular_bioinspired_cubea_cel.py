# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_cellular_bioinspired_materiala_cellular_bioinspired_cubea_cel" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with smooth edges and with sandwich layers using blender script

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the sandwich structure
strut_thickness = 0.3  # Thickness of the struts
smooth_level = 2        # Level of smoothness
slab_thickness = 0.25   # Thickness of the slabs

def build_sandwich_structure():
    # Build a smooth cellular sandwich structure.
    # Process:
    # 1. Create a cube as the base.
    # 2. Fracture the cube into smaller pieces.
    # 3. Merge the pieces into a single object.
    # 4. Apply wireframe modifier for cellular appearance.
    # 5. Apply subsurface modifier for smoothness.
    # 6. Add top and bottom slabs to finalize the sandwich.

    # Enable Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    # Scale the cube
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Apply fracture operation
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
    bpy.data.objects.remove(cube, do_unlink=True)

    # Select all fractured objects
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

    # Clean geometry
    if bpy.context.selected_objects:
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
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
        subsurf_mod.levels = smooth_level
        subsurf_mod.render_levels = smooth_level

    # Calculate positions for slabs
    slab_height = 1.5
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

# Build the sandwich structure
build_sandwich_structure()
