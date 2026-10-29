# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_builds_a_model_of_a_cellular_cube_with_smooth_edges_an" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that builds a model of a cellular cube with smooth edges and with sandwich layers. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cell_thickness = 0.1  # Thickness of struts
smoothing_factor = 5   # Level of smoothness
slab_size = 0.3       # Size of the sandwich slabs

def construct_cellular_sandwich():
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add()
    cube_base = bpy.context.active_object

    cube_base.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

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

    if cube_base and cube_base.name in bpy.data.objects:
        bpy.data.objects.remove(cube_base, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    first_mesh_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_mesh_obj is None:
                first_mesh_obj = obj
    if first_mesh_obj:
        bpy.context.view_layer.objects.active = first_mesh_obj
        bpy.ops.object.join()

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.type == 'MESH':
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = cell_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothing_factor
        subsurf_mod.render_levels = smoothing_factor

    wireframe_height = 1.5
    bottom_slab_position = -wireframe_height / 2 - slab_size / 2
    top_slab_position = wireframe_height / 2 + slab_size / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

construct_cellular_sandwich()
