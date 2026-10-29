# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_python_blender_code_that_creates_a_model_of_a_cellular_structure_with_smo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create python blender code that creates a model of a cellular structure with smooth curves. Think step by step.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular structure
thickness_value = 0.3  # Thickness of the struts
smoothness_value = 1  # Level of smoothness

def create_structure():
    addon_utils.enable("object_fracture_cell")
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_object = bpy.context.object
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
    bpy.data.objects.remove(cube_object, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for obj in mesh_objects:
        obj.select_set(True)
    if mesh_objects:
        bpy.context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.join()
    active_mesh = bpy.context.view_layer.objects.active
    if active_mesh:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = thickness_value
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothness_value
        subsurf_mod.render_levels = smoothness_value

# Run the structure creation function
create_structure()
