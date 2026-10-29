# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_a_cellular_bioinspired_materiala_cellul" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with layers on top and bottom

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.3
slab_thickness = 0.1

def enable_addons():
    addon_utils.enable('object_fracture_cell')

def create_cube():
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    return cube

def fracture_and_join(cube):
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
    join_meshes()

def join_meshes():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()
    apply_wireframe()

def apply_wireframe():
    active_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')
    wf_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
    wf_modifier.thickness = strut_thickness
    wf_modifier.offset = -1
    wf_modifier.use_even_offset = False
    wf_modifier.use_relative_offset = True
    wf_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')
    create_sandwich_slabs()

def create_sandwich_slabs():
    height = 1.5
    bottom_z = -height / 2 - slab_thickness / 2
    top_z = height / 2 + slab_thickness / 2
    create_slab(bottom_z)
    create_slab(top_z)

def create_slab(z_position):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    slab = bpy.context.active_object
    slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Main execution flow
enable_addons()
cube = create_cube()
fracture_and_join(cube)
