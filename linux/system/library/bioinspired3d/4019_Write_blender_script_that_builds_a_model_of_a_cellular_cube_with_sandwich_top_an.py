# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_builds_a_model_of_a_cellular_cube_with_sandwich_top_an" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that builds a model of a cellular cube with sandwich top and bottom layers Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_size = 0.1
slab_size = 0.4

def make_cellular_sandwich():
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    cube.scale = (1, 1, 0.75)
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
        use_remove_original=True
    )

    if cube and cube.name in bpy.data.objects:
        bpy.data.objects.remove(cube, do_unlink=True)

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

    if bpy.context.selected_objects:
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_size
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

    height_of_wireframe = 1.5
    bottom_slab_z = -height_of_wireframe / 2 - slab_size / 2
    top_slab_z = height_of_wireframe / 2 + slab_size / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

make_cellular_sandwich()
