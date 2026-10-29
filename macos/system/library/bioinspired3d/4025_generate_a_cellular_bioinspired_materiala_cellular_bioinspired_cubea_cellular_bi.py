# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_cellular_bioinspired_materiala_cellular_bioinspired_cubea_cellular_bi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with sandwich layers using a Blender code think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Sandwich parameters
strut_thickness = 0.3  # Thickness of the struts
slab_thickness = 0.05  # Thickness of the top and bottom slabs

def assemble_cellular_sandwich():
    # Enable Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Add a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
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

    # Select fractured pieces
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
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Define slab positions
    sandwich_height = 1.5
    bottom_slab_z = -sandwich_height / 2 - slab_thickness / 2
    top_slab_z = sandwich_height / 2 + slab_thickness / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Assemble the sandwich structure
assemble_cellular_sandwich()
