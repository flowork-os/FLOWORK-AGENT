# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_code_in_Blender_that_builds_a_model_of_a_cellular_bioinspired_materiala_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create code in Blender that builds a model of a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the thickness for the cellular structure
strut_thickness = 0.2

class CellularStructure:
    @staticmethod
    def create():
        # Activate the Fracture Cell add-on
        addon_utils.enable("object_fracture_cell")
        
        # Add a cube as the base shape
        bpy.ops.mesh.primitive_cube_add(size=2)
        base_cube = bpy.context.object
        
        # Execute the Fracture Cell operation
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
        if base_cube and base_cube.name in bpy.data.objects:
            bpy.data.objects.remove(base_cube, do_unlink=True)
        
        # Join all fractured parts
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
        
        if bpy.context.selected_objects:
            active_mesh = bpy.context.view_layer.objects.active
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.2)
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.mesh.dissolve_limited(angle_limit=1)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Add Wireframe Modifier
            wire_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
            wire_mod.thickness = strut_thickness
            wire_mod.offset = -1
            wire_mod.use_even_offset = False
            wire_mod.use_relative_offset = True
            wire_mod.use_replace = True

# Create the cellular structure
CellularStructure.create()
