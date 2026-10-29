# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender__create_a_model_of_a_cellular_cube_with_smooth_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender, create a model of a cellular cube with smooth edges.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration settings
thickness_value = 0.1
subdivision_level = 6

def build_cellular_structure():
    # Function to build a smooth cellular structure.
    # Outline:
    # 1. Begin with a cube.
    # 2. Fracture the cube into smaller sections.
    # 3. Create a wireframe from the fractured pieces.
    # 4. Smooth edges using a subdivision surface.

    # Enable the Fracture Cell add-on
    addon_utils.enable('object_fracture_cell')

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_base = bpy.context.object

    # Execute the fracture operation
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

    # Remove the original cube after fracturing
    if cube_base and cube_base.name in bpy.data.objects:
        bpy.data.objects.remove(cube_base, do_unlink=True)

    # Deselect all objects
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

    if bpy.context.selected_objects and bpy.context.view_layer.objects.active:
        active_mesh = bpy.context.view_layer.objects.active
        # Clean up the mesh geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Wireframe Modifier
        wireframe_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_modifier.thickness = thickness_value
        wireframe_modifier.offset = -1
        wireframe_modifier.use_even_offset = False
        wireframe_modifier.use_relative_offset = True
        wireframe_modifier.use_replace = True

        # Subsurface Modifier
        subsurf_modifier = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = subdivision_level
        subsurf_modifier.render_levels = subdivision_level

# Build the cellular structure
build_cellular_structure()
