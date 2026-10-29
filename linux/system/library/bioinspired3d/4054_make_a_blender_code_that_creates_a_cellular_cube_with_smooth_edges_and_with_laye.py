# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_blender_code_that_creates_a_cellular_cube_with_smooth_edges_and_with_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a blender code that creates a cellular cube with smooth edges and with layers on top and bottom Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

thickness_value = 0.25
smoothness_value = 2
size_value = 0.1

def create_cellular_structure():
    addon_utils.enable("object_fracture_cell")

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
        use_remove_original=True,
        collection_name="",
        use_debug_points=False,
        use_debug_redraw=True,
        use_debug_bool=False
    )

    bpy.data.objects.remove(cube, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.object.join()

    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_modifier.thickness = thickness_value
    wireframe_modifier.offset = -1
    wireframe_modifier.use_even_offset = False
    wireframe_modifier.use_relative_offset = True
    wireframe_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')

    subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_modifier.levels = smoothness_value
    subsurf_modifier.render_levels = smoothness_value

    create_sandwich_slabs()

def create_sandwich_slabs():
    height = 1.5
    bottom_position = -height / 2 - size_value / 2
    top_position = height / 2 + size_value / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, size_value / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, size_value / 2)
    bpy.ops.object.transform_apply(scale=True)

create_cellular_structure()
