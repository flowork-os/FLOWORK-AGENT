# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__create_a_cellular_bioinspired_materiala_cellular_bioinspired" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, create a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure smoothed and with sandwich top and bottom layers.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
strut_thickness = 0.2
smoothness_level = 3
slab_thickness = 0.1

# Function to create a cellular sandwich structure

def generate_cellular_sandwich():
    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube into smaller parts
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
    bpy.data.objects.remove(base_cube, do_unlink=True)

    # Combine fractured parts
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean up geometry
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply modifiers for wireframe and subsurface
    wire_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wire_mod.thickness = strut_thickness
    wire_mod.offset = -1
    wire_mod.use_relative_offset = True
    bpy.ops.object.convert(target='MESH')

    sub_mod = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    sub_mod.levels = smoothness_level
    sub_mod.render_levels = smoothness_level

    # Define positions for the slabs
    height_of_wireframe = 1.5
    bottom_slab_z = -height_of_wireframe / 2 - slab_thickness / 2
    top_slab_z = height_of_wireframe / 2 + slab_thickness / 2

    # Create bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Create top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Execute the function to create the structure
generate_cellular_sandwich()
