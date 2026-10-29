# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_cellular_structure_with_sandwich_top_and_bottom_layers_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a cellular structure with sandwich top and bottom layers in blender script think step by step.

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specifications for the sandwich model
strut_width = 0.15  # Width of the struts
slab_height = 0.3   # Height of the top and bottom slabs

# Function to construct the sandwich model
def construct_sandwich():
    # Activate the Fracture Cell add-on
    addon_utils.enable("object_fracture_cell")

    # Create the initial cube
    bpy.ops.mesh.primitive_cube_add()
    initial_cube = bpy.context.active_object

    # Scale the cube appropriately
    initial_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Apply the Fracture Cell operation
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
    bpy.data.objects.remove(initial_cube, do_unlink=True)

    # Select and join fractured objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.object.join()

    # Geometry cleanup
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply Wireframe Modifier
    wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_modifier.thickness = strut_width
    wireframe_modifier.offset = -1
    wireframe_modifier.use_even_offset = False
    wireframe_modifier.use_relative_offset = True
    wireframe_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Calculate positions for slabs
    slab_thickness = 1.5
    bottom_slab_z = -slab_thickness / 2 - slab_height / 2
    top_slab_z = slab_thickness / 2 + slab_height / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_height / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_height / 2)
    bpy.ops.object.transform_apply(scale=True)

# Run the sandwich construction
construct_sandwich()
