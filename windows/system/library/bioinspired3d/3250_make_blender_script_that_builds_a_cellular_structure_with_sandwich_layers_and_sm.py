# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_script_that_builds_a_cellular_structure_with_sandwich_layers_and_sm" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender script that builds a cellular structure with sandwich layers and smoothed

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular sandwich structure
cell_thickness = 0.2
smoothness = 6
slab_size = 0.05

# Function to build the sandwich

def build_cellular_sandwich():
    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add()
    base_cube = bpy.context.active_object
    base_cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Fracture the cube
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

    # Combine all mesh objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean geometry
    active_object = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply modifiers
    wireframe_mod = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = cell_thickness
    wireframe_mod.offset = -1
    wireframe_mod.use_relative_offset = True
    bpy.ops.object.convert(target='MESH')

    subsurf_mod = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_mod.levels = smoothness
    subsurf_mod.render_levels = smoothness

    # Create sandwich slabs
    slab_positions = [-0.75 - slab_size / 2, 0.75 + slab_size / 2]
    for position in slab_positions:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, slab_size / 2)
        bpy.ops.object.transform_apply(scale=True)

# Execute the sandwich building function
build_cellular_sandwich()
