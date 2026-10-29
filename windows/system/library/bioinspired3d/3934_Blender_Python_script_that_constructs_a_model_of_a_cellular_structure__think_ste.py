# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_constructs_a_model_of_a_cellular_structure__think_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that constructs a model of a cellular structure. think step by step

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set strut thickness
wire_thickness = 0.1

def create_cell_structure():
    # Enable the required add-on
    addon_utils.enable("object_fracture_cell")
    
    # Add a cube
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube_obj = bpy.context.object
    
    # Apply the fracturing
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
    if cube_obj and cube_obj.name in bpy.data.objects:
        bpy.data.objects.remove(cube_obj, do_unlink=True)
    
    # Select and join all fractured pieces
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    
    if bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()
        
        # Clean up the mesh
        clean_up_mesh()

def clean_up_mesh():
    active_mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.mesh.dissolve_limited(angle_limit=1)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Apply Wireframe Modifier
    wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
    wireframe_mod.thickness = wire_thickness
    wireframe_mod.offset = -1
    wireframe_mod.use_even_offset = False
    wireframe_mod.use_relative_offset = True
    wireframe_mod.use_replace = True

# Execute the creation of the cell structure
create_cell_structure()
