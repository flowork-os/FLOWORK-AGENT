# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_make_a_cellular_structure_with_sandwich_top_and_bottom_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to make a cellular structure with sandwich top and bottom layers. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.2  # Thickness of the struts
slab_thickness = 0.1    # Thickness of the top and bottom slabs

# Function to build the sandwich structure
def build_sandwich():
    # Initialize Fracture Cell add-on
    addon_utils.enable("object_fracture_cell")

    # Add a cube to serve as the base object
    bpy.ops.mesh.primitive_cube_add()
    cube_object = bpy.context.active_object

    # Adjust the scale of the cube
    cube_object.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Execute the Fracture operation
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

    # Remove original cube
    bpy.data.objects.remove(cube_object, do_unlink=True)

    # Select all mesh objects for joining
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.object.join()

    # Clean up geometry
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create Wireframe Modifier
    wireframe_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = strut_thickness
    wireframe_mod.offset = -1
    wireframe_mod.use_even_offset = False
    wireframe_mod.use_relative_offset = True
    wireframe_mod.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Define positions for the slabs
    slab_height = 1.5
    bottom_slab_position = -slab_height / 2 - slab_thickness / 2
    top_slab_position = slab_height / 2 + slab_thickness / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_position))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_position))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the structure creation
build_sandwich()
