# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_cellular_bioinspired_materiala_cellular_bioinspired_cubea_cellular_bioi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure smoothed and with sandwich top and bottom layers in blender python code Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cell_thickness = 0.25
smooth_factor = 5
slab_height = 0.3

def build_cellular_structure():
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object
    base_cube.scale = (1, 1, 0.75)
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

    bpy.data.objects.remove(base_cube, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    wire_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wire_mod.thickness = cell_thickness
    wire_mod.offset = -1
    wire_mod.use_even_offset = False
    wire_mod.use_relative_offset = True
    wire_mod.use_replace = True
    bpy.ops.object.convert(target='MESH')

    sub_mod = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    sub_mod.levels = smooth_factor
    sub_mod.render_levels = smooth_factor

    height = 1.5
    bottom_slab_z = -height / 2 - slab_height / 2
    top_slab_z = height / 2 + slab_height / 2
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_height / 2)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_height / 2)
    bpy.ops.object.transform_apply(scale=True)

build_cellular_structure()
