# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_blender_code_make_a_model_of_a_cellular_cube_with_sandwich_top_and_botto" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a blender code make a model of a cellular cube with sandwich top and bottom layers. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_thickness_value = 0.25
slab_thickness_value = 0.15

def build_cellular_sandwich():
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
        use_remove_original=True
    )

    if cube_base and cube_base.name in bpy.data.objects:
        bpy.data.objects.remove(cube_base, do_unlink=True)

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

        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_thickness_value
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    wireframe_height_value = 1.5
    bottom_slab_position_value = -wireframe_height_value / 2 - slab_thickness_value / 2
    top_slab_position_value = wireframe_height_value / 2 + slab_thickness_value / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position_value))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness_value / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position_value))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness_value / 2)
    bpy.ops.object.transform_apply(scale=True)

build_cellular_sandwich()
