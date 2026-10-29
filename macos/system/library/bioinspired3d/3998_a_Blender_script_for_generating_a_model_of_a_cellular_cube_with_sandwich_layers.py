# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_generating_a_model_of_a_cellular_cube_with_sandwich_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for generating a model of a cellular cube with sandwich layers. think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_thickness_value = 0.3  # Thickness of the struts
slab_thickness_value = 0.05  # Thickness of the sandwich slabs

def assemble_sandwich():
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add()
    cube_object = bpy.context.active_object

    cube_object.scale = (1, 1, 0.75)
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

    if cube_object and cube_object.name in bpy.data.objects:
        bpy.data.objects.remove(cube_object, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    fractured_meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for mesh in fractured_meshes:
        mesh.select_set(True)
    if fractured_meshes:
        bpy.context.view_layer.objects.active = fractured_meshes[0]
        bpy.ops.object.join()

    active_mesh = bpy.context.view_layer.objects.active
    if active_mesh and active_mesh.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_thickness_value
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

    height_of_sandwich = 1.5  # Height of the sandwich
    bottom_slab_position = -height_of_sandwich / 2 - slab_thickness_value / 2
    top_slab_position = height_of_sandwich / 2 + slab_thickness_value / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness_value / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness_value / 2)
    bpy.ops.object.transform_apply(scale=True)

assemble_sandwich()
