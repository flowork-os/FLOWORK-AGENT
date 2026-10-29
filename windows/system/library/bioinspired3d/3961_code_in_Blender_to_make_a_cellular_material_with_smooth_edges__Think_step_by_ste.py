# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_make_a_cellular_material_with_smooth_edges__Think_step_by_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to make a cellular material with smooth edges. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure
strut_thickness = 0.15  # Thickness of the struts
smoothing_level = 3  # Level of smoothness

class CellularStructure:
    @staticmethod
    def create():
        addon_utils.enable("object_fracture_cell")
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube_object = bpy.context.object
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
        if cube_object and cube_object.name in bpy.data.objects:
            bpy.data.objects.remove(cube_object, do_unlink=True)
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
        active_mesh = bpy.context.view_layer.objects.active
        if active_mesh and active_mesh.type == 'MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.2)
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.mesh.dissolve_limited(angle_limit=1)
            bpy.ops.object.mode_set(mode='OBJECT')
            wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
            wireframe_mod.thickness = strut_thickness
            wireframe_mod.offset = -1
            wireframe_mod.use_even_offset = False
            wireframe_mod.use_relative_offset = True
            wireframe_mod.use_replace = True
            subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
            subsurf_mod.levels = smoothing_level
            subsurf_mod.render_levels = smoothing_level

# Create the cellular structure
CellularStructure.create()
