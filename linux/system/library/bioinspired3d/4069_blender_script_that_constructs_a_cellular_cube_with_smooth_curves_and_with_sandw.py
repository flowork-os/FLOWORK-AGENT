# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_constructs_a_cellular_cube_with_smooth_curves_and_with_sandw" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that constructs a cellular cube with smooth curves and with sandwich layers think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cell_strut_thickness = 0.1
subdivision_level = 2
slab_height = 0.4

def create_cellular_structure():
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add()
    initial_cube = bpy.context.active_object
    initial_cube.scale = (1, 1, 0.75)
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

    bpy.data.objects.remove(initial_cube, do_unlink=True)

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

    wireframe = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe.thickness = cell_strut_thickness
    wireframe.offset = -1
    wireframe.use_relative_offset = True
    bpy.ops.object.convert(target='MESH')

    subsurf = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf.levels = subdivision_level
    subsurf.render_levels = subdivision_level

    slab_positions = [-0.75 - slab_height / 2, 0.75 + slab_height / 2]
    for position in slab_positions:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, slab_height / 2)
        bpy.ops.object.transform_apply(scale=True)

create_cellular_structure()
