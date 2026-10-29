# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code_create_a_cellular_material_with_sandwich_top_and_bottom_lay" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code create a cellular material with sandwich top and bottom layers. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_width = 0.25  # Thickness of the struts
slab_thickness = 0.2  # Thickness of the top and bottom slabs

def setup_scene():
    addon_utils.enable('object_fracture_cell')
    cube = bpy.ops.mesh.primitive_cube_add()
    return bpy.context.active_object

def scale_cube(cube):
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

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
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

def clean_mesh():
    active_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

def apply_wireframe_mod():
    active_mesh = bpy.context.view_layer.objects.active
    wire_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wire_mod.thickness = strut_width
    wire_mod.offset = -1
    bpy.ops.object.convert(target='MESH')

def create_slab(z_position):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    slab = bpy.context.active_object
    slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

initial_cube = setup_scene()
scale_cube(initial_cube)
fracture_cube(initial_cube)
join_fragments()
clean_mesh()
apply_wireframe_mod()
create_slab(-1.5)
create_slab(1.5)
