# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_script_that_constructs_a_cellular_bioinspired_materiala_cellular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender script that constructs a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure smoothed. Think step by step.

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the cellular model
width = 0.1  # Strut thickness
level_of_smoothness = 2  # Smoothing level

class Structure:
    def __init__(self, thickness, smoothness):
        self.thickness = thickness
        self.smoothness = smoothness

    def build(self):
        addon_utils.enable("object_fracture_cell")
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube = bpy.context.object
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
        bpy.data.objects.remove(cube, do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
        bpy.ops.object.join()
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        wf_modifier = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = self.thickness
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True
        subsurf_modifier = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = self.smoothness
        subsurf_modifier.render_levels = self.smoothness

# Create and build the structure
cell_structure = Structure(width, level_of_smoothness)
cell_structure.build()
