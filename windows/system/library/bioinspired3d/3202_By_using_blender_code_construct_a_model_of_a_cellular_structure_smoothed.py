# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code_construct_a_model_of_a_cellular_structure_smoothed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code construct a model of a cellular structure smoothed

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define structure characteristics
cylinder_thickness = 0.25  # Thickness of the struts
smoothing_level = 5  # Level of smoothness

def build_cell_structure():
    # Initialize the Fracture Cell add-on
    addon_utils.enable("object_fracture_cell")
    bpy.ops.mesh.primitive_cube_add(size=2)
    base_cube = bpy.context.object

    # Fracture cube into smaller pieces
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

    # Remove the original cube
    bpy.data.objects.remove(base_cube, do_unlink=True)

    # Select fractured pieces and join
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean up geometry
    if bpy.context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe Modifier
        wireframe_mod = bpy.context.view_layer.objects.active.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = cylinder_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True

        # Add Subdivision Modifier
        subsurf_mod = bpy.context.view_layer.objects.active.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = smoothing_level
        subsurf_mod.render_levels = smoothing_level

# Execute the function to build the structure
build_cell_structure()
