# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code_construct_a_cellular_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code construct a cellular material. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cell_thickness = 0.15

def setup_fracture_cell():
    addon_utils.enable('object_fracture_cell')

def generate_cube():
    bpy.ops.mesh.primitive_cube_add(size=2)
    return bpy.context.object

def fracture_cube(cube):
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
    bpy.data.objects.remove(cube, do_unlink=True)

def join_mesh_objects():
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

def clean_up_mesh():
    active_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

def apply_wireframe():
    active_obj = bpy.context.view_layer.objects.active
    wireframe = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe.thickness = cell_thickness
    wireframe.offset = -1
    wireframe.use_even_offset = False
    wireframe.use_relative_offset = True
    wireframe.use_replace = True

setup_fracture_cell()
cube = generate_cube()
fracture_cube(cube)
join_mesh_objects()
clean_up_mesh()
apply_wireframe()
