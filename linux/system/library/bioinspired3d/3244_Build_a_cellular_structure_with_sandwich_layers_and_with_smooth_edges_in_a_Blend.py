# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_cellular_structure_with_sandwich_layers_and_with_smooth_edges_in_a_Blend" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a cellular structure with sandwich layers and with smooth edges in a Blender script

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the sandwich structure
strut_width = 0.1
subsurf_level = 6
slab_thickness = 0.4

def generate_sandwich():
    # Enable the required add-on
    addon_utils.enable('object_fracture_cell')

    # Create base cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = (1, 1, 0.75)
    bpy.ops.object.transform_apply(scale=True)

    # Apply Fracture Cell
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
        collection_name='',
        use_debug_points=False,
        use_debug_redraw=True,
        use_debug_bool=False
    )

    # Remove original cube
    bpy.data.objects.remove(cube, do_unlink=True)

    # Merge fractured objects
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

    # Add Wireframe Modifier
    wf_modifier = active_object.modifiers.new(name='Wireframe', type='WIREFRAME')
    wf_modifier.thickness = strut_width
    wf_modifier.offset = -1
    wf_modifier.use_even_offset = False
    wf_modifier.use_relative_offset = True
    wf_modifier.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Add Subsurface Modifier
    subsurf_modifier = active_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf_modifier.levels = subsurf_level
    subsurf_modifier.render_levels = subsurf_level

    # Create sandwich slabs
    height = 1.5
    bottom_slab_location = -height / 2 - slab_thickness / 2
    top_slab_location = height / 2 + slab_thickness / 2
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_location))
    bottom_slab = bpy.context.active_object
    bottom_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_location))
    top_slab = bpy.context.active_object
    top_slab.scale = (1, 1, slab_thickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Run the function to generate the sandwich
generate_sandwich()
