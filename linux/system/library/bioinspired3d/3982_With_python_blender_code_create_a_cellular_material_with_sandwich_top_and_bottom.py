# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code_create_a_cellular_material_with_sandwich_top_and_bottom" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code create a cellular material with sandwich top and bottom layers think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_width = 0.15  # Width of struts
slab_height = 0.25  # Height of the sandwich slabs

def generate_sandwich_structure():
    """Constructs a cellular sandwich structure."""
    addon_utils.enable("object_fracture_cell")

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
        collection_name="",
        use_debug_points=False,
        use_debug_redraw=True,
        use_debug_bool=False
    )

    if cube_base and cube_base.name in bpy.data.objects:
        bpy.data.objects.remove(cube_base, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    first_mesh_object = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if first_mesh_object is None:
                first_mesh_object = obj
    if first_mesh_object:
        bpy.context.view_layer.objects.active = first_mesh_object
        bpy.ops.object.join()

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active:
        active_object = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        wireframe_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_width
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')

    height_of_sandwich = 1.5  # Height of the sandwich
    bottom_position = -height_of_sandwich / 2 - slab_height / 2
    top_position = height_of_sandwich / 2 + slab_height / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_position))
    bottom_slab_object = bpy.context.active_object
    bottom_slab_object.scale = (1, 1, slab_height / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_position))
    top_slab_object = bpy.context.active_object
    top_slab_object.scale = (1, 1, slab_height / 2)
    bpy.ops.object.transform_apply(scale=True)

generate_sandwich_structure()
