# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code_make_a_model_of_a_cellular_material_with_smooth_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code make a model of a cellular material with smooth edges

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cellular structure
cell_thickness = 0.15
smoothing_level = 4

class CellularModel:
    def __init__(self, thickness, smooth_level):
        self.thickness = thickness
        self.smooth_level = smooth_level

    def build_structure(self):
        addon_utils.enable("object_fracture_cell")
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube = bpy.context.object

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
        if cube and cube.name in bpy.data.objects:
            bpy.data.objects.remove(cube, do_unlink=True)

        # Join fractured objects
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()

        # Clean up geometry
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Wireframe modifier
        wf_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = self.thickness
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True

        # Subsurface modifier
        subsurf_modifier = active_obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = self.smooth_level
        subsurf_modifier.render_levels = self.smooth_level

# Create and build the cellular model
cell_model = CellularModel(cell_thickness, smoothing_level)
cell_model.build_structure()
