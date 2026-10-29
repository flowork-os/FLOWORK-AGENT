# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_a_model_of_a_cellular_structure_with_smooth_curves" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates a model of a cellular structure with smooth curves. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the cellular mesh
mesh_thickness = 0.25  # Thickness of the struts
smoothness_setting = 5   # Level of smoothness

def generate_cellular_geometry():
    # Activate the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    base_cube = bpy.context.object

    # Fracture the cube
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

    # Remove the original cube after fracturing
    bpy.data.objects.remove(base_cube, do_unlink=True)

    # Join all fractured pieces
    join_all_meshes()

def join_all_meshes():
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
        clean_mesh_geometry()

def clean_mesh_geometry():
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2) 
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')
    apply_mesh_modifiers(active_mesh)

def apply_mesh_modifiers(obj):
    wireframe = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe.thickness = mesh_thickness
    wireframe.offset = -1
    wireframe.use_even_offset = False
    wireframe.use_relative_offset = True
    wireframe.use_replace = True

    subsurf = obj.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf.levels = smoothness_setting
    subsurf.render_levels = smoothness_setting

# Generate the cellular geometry
generate_cellular_geometry()
