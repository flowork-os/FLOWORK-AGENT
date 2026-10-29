# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_cellular_bioinspired_materiala_cellular_bioinspired_cubea_cellular_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure smoothed and with sandwich top and bottom layers using a blender code think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_thickness = 0.1  # Thickness of the struts
smoothness_level = 2  # Level of smoothness
slab_thickness = 0.35  # Thickness of the top and bottom slabs

def create_sandwich_structure():
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

    active_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    wf_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wf_modifier.thickness = strut_thickness
    wf_modifier.offset = -1
    bpy.ops.object.convert(target='MESH')

    subsurf_modifier = active_obj.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_modifier.levels = smoothness_level
    subsurf_modifier.render_levels = smoothness_level

    slab_height = 1.5
    bottom_slab_z = -slab_height / 2 - slab_thickness / 2
    top_slab_z = slab_height / 2 + slab_thickness / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

create_sandwich_structure()
