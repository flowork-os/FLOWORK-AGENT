# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_cellular_structure_with_sandwich_layers_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a cellular structure with sandwich layers in blender code

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.2  # Thickness of the struts
slab_thickness = 0.3  # Thickness of the top and bottom slabs

# Function to create the sandwich structure

def build_cellular_sandwich():
    # Setup: Create a cube and fracture it
    addon_utils.enable('object_fracture_cell')
    bpy.ops.mesh.primitive_cube_add()
    cube_obj = bpy.context.active_object
    cube_obj.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    fractured_cube = bpy.context.object

    # Fracturing the cube into smaller pieces
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

    # Remove original cube
    if fractured_cube.name in bpy.data.objects:
        bpy.data.objects.remove(fractured_cube, do_unlink=True)

    # Join fractured pieces into a single object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean up geometry
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Wireframe modifier application
    wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = strut_thickness
    wireframe_mod.offset = -1
    wireframe_mod.use_relative_offset = True
    bpy.ops.object.convert(target='MESH')

    # Creating the sandwich slabs
    slab_height = 1.5
    bottom_z = -slab_height / 2 - slab_thickness / 2
    top_z = slab_height / 2 + slab_thickness / 2

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to create the structure
build_cellular_sandwich()
