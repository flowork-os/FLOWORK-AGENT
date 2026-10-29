# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code_create_a_cellular_structure_with_layers_on_top_and_bottom_Thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code create a cellular structure with layers on top and bottom Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.2  # Thickness of the struts
slab_thickness = 0.1  # Thickness of the top and bottom sandwich slabs

def generate_cellular_sandwich():
    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object

    # Scale the cube
    base_cube.scale = (1, 1, 0.75)
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
        use_remove_original=True
    )

    # Remove the original cube
    if base_cube and base_cube.name in bpy.data.objects:
        bpy.data.objects.remove(base_cube, do_unlink=True)

    # Join fractured pieces into one object
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

    # Clean up geometry
    if bpy.context.selected_objects:
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Create Wireframe Modifier
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = strut_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    # Create bottom and top slabs
    slab_height = 1.5  # Height of the object to be sandwiched
    bottom_slab_loc = -slab_height / 2 - slab_thickness / 2
    top_slab_loc = slab_height / 2 + slab_thickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_loc))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_loc))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to create the sandwich structure
generate_cellular_sandwich()
