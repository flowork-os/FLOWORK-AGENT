# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_generate_a_model_of_a_cellular_cube_with_smooth_edges__Th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script generate a model of a cellular cube with smooth edges. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_width = 0.25  # Width of the struts
smoothness = 2      # Smoothing level

def build_cell_structure():
    addon_utils.enable('object_fracture_cell')

    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_base = bpy.context.object
    
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
    fractured_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for obj in fractured_objects:
        obj.select_set(True)
    if fractured_objects:
        bpy.context.view_layer.objects.active = fractured_objects[0]
        bpy.ops.object.join()
    
    if bpy.context.selected_objects:
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        wireframe_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = strut_width
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True

        subsurf_modifier = active_obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smoothness
        subsurf_modifier.render_levels = smoothness

build_cell_structure()
