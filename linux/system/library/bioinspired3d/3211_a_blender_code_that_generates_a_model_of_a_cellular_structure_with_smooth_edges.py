# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_generates_a_model_of_a_cellular_structure_with_smooth_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that generates a model of a cellular structure with smooth edges

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Setting parameters for the cellular model
strut_width = 0.2  # Width of the struts
smooth_level = 5  # Level of smoothness

def create_cell_structure():
    addon_utils.enable("object_fracture_cell")
    bpy.ops.mesh.primitive_cube_add(size=2)
    base_cube = bpy.context.object
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
    if base_cube:
        bpy.data.objects.remove(base_cube, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_items = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for item in mesh_items:
        item.select_set(True)
    if mesh_items:
        bpy.context.view_layer.objects.active = mesh_items[0]
        bpy.ops.object.join()
    active_object = bpy.context.view_layer.objects.active
    if active_object:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        wf_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = strut_width
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True
        subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = smooth_level
        subsurf_modifier.render_levels = smooth_level

# Execute the function to create the model
create_cell_structure()
