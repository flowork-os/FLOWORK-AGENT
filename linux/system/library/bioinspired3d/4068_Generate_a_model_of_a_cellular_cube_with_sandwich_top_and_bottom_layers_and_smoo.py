# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_cellular_cube_with_sandwich_top_and_bottom_layers_and_smoo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a cellular cube with sandwich top and bottom layers and smoothed in blender script think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

thickness_value = 0.15
smooth_level = 5
sandwich_thickness = 0.2

def build_sandwich():
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

    bpy.data.objects.remove(cube, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_modifier.thickness = thickness_value
    wireframe_modifier.offset = -1
    wireframe_modifier.use_relative_offset = True
    bpy.ops.object.convert(target='MESH')

    subsurf_modifier = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_modifier.levels = smooth_level
    subsurf_modifier.render_levels = smooth_level

    slab_positions = [-0.75 - sandwich_thickness / 2, 0.75 + sandwich_thickness / 2]
    for position in slab_positions:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, sandwich_thickness / 2)
        bpy.ops.object.transform_apply(scale=True)

build_sandwich()
