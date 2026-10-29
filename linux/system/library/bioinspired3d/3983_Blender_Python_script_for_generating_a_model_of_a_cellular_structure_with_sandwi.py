# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_a_model_of_a_cellular_structure_with_sandwi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating a model of a cellular structure with sandwich top and bottom layers. Think step by step.

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Cellular sandwich parameters
strut_size = 0.25  # Width of struts
slab_thickness = 0.1  # Thickness of top and bottom slabs

def cellular_sandwich():
    """Creates a cellular sandwich structure."""
    # Activate the Fracture Cell add-on
    addon_utils.enable("object_fracture_cell")

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object

    # Adjust the cube size
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube into pieces
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

    # Delete the original cube
    if cube and cube.name in bpy.data.objects:
        bpy.data.objects.remove(cube, do_unlink=True)

    # Select fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    fractured_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    for obj in fractured_objects:
        obj.select_set(True)
    if fractured_objects:
        bpy.context.view_layer.objects.active = fractured_objects[0]
        bpy.ops.object.join()

    # Clean up geometry
    if bpy.context.selected_objects:
        active_object = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add wireframe modifier
        wireframe_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_size
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Create slabs at calculated positions
    height = 1.5  # Height of the sandwich
    bottom_slab_z = -height / 2 - slab_thickness / 2
    top_slab_z = height / 2 + slab_thickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Create the cellular sandwich
cellular_sandwich()
