# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_blender_code_that_generates_a_cellular_structure_with_layers_on_top_and" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a blender code that generates a cellular structure with layers on top and bottom. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_size = 0.1
slab_size = 0.4

def setup_scene():
    addon_utils.enable('object_fracture_cell')

def create_base_cube():
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    return cube

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
        use_remove_original=True
    )
    bpy.data.objects.remove(cube, do_unlink=True)

def join_fragments():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

def apply_wireframe():
    active_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')
    wf_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wf_modifier.thickness = strut_size
    wf_modifier.offset = -1
    wf_modifier.use_even_offset = False
    wf_modifier.use_relative_offset = True
    wf_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')

def create_slab(z_position):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    slab = bpy.context.active_object
    slab.scale = (1, 1, slab_size / 2)
    bpy.ops.object.transform_apply(scale=True)

setup_scene()
base_cube = create_base_cube()
fracture_cube(base_cube)
join_fragments()
apply_wireframe()

height = 1.5
create_slab(-height / 2 - slab_size / 2)
create_slab(height / 2 + slab_size / 2)
