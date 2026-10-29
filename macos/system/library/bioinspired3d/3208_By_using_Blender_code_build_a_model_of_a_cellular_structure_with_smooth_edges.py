# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code_build_a_model_of_a_cellular_structure_with_smooth_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code build a model of a cellular structure with smooth edges.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define mesh parameters
cell_strut_thickness = 0.1  # Thickness of the struts
mesh_smoothness = 6          # Level of smoothness

def build_cellular_structure():
    # Enable Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_base = bpy.context.object

    # Execute fracturing
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

    # Clean up the original cube
    bpy.data.objects.remove(cube_base, do_unlink=True)

    # Join all fragments together
    combine_fragments()

def combine_fragments():
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
        finalize_mesh()

def finalize_mesh():
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2) 
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')
    apply_modifiers(active_object)

def apply_modifiers(obj):
    wireframe_mod = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = cell_strut_thickness
    wireframe_mod.offset = -1
    wireframe_mod.use_even_offset = False
    wireframe_mod.use_relative_offset = True
    wireframe_mod.use_replace = True

    subsurf_mod = obj.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_mod.levels = mesh_smoothness
    subsurf_mod.render_levels = mesh_smoothness

# Build the cellular structure
build_cellular_structure()
