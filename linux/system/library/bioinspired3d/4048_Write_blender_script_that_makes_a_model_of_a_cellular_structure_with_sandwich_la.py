# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_makes_a_model_of_a_cellular_structure_with_sandwich_la" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that makes a model of a cellular structure with sandwich layers and with smooth edges. Think step by step

import bpy
import addon_utils

# Clear the scene of all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Constants for the sandwich design
strutThickness = 0.25  # Thickness of the struts
smoothLevel = 5  # Level of smoothness
slabThickness = 0.4  # Thickness of the top and bottom slabs

def generateSandwich():
    # Create a smooth cellular sandwich structure
    addon_utils.enable("object_fracture_cell")

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = (1, 1, 0.75)
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
        use_remove_original=True,
        collection_name="",
        use_debug_points=False,
        use_debug_redraw=True,
        use_debug_bool=False
    )

    # Remove the original cube
    bpy.data.objects.remove(cube, do_unlink=True)

    # Join all fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    # Clean up geometry
    active = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Wireframe Modifier
    wireframe = active.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe.thickness = strutThickness
    wireframe.offset = -1
    wireframe.use_even_offset = False
    wireframe.use_relative_offset = True
    wireframe.use_replace = True
    bpy.ops.object.convert(target='MESH')

    # Subdivision Modifier
    subsurf = active.modifiers.new(name='Subdivision', type='SUBSURF')
    subsurf.levels = smoothLevel
    subsurf.render_levels = smoothLevel

    # Create slabs
    slabHeight = 1.5
    bottomZ = -slabHeight / 2 - slabThickness / 2
    topZ = slabHeight / 2 + slabThickness / 2

    # Bottom slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottomZ))
    bottomSlab = bpy.context.active_object
    bottomSlab.scale = (1, 1, slabThickness / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Top slab
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, topZ))
    topSlab = bpy.context.active_object
    topSlab.scale = (1, 1, slabThickness / 2)
    bpy.ops.object.transform_apply(scale=True)

# Run the function to create the sandwich
generateSandwich()
