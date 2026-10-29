# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_builds_a_cellular_material_smoothed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that builds a cellular material smoothed.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the structure
cell_thickness = 0.15  # Thickness of struts
smoothness_degree = 4  # Smoothness level for the model

class CellularModel:
    def __init__(self, thickness, smoothness):
        self.thickness = thickness
        self.smoothness = smoothness

    def create(self):
        addon_utils.enable("object_fracture_cell")
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube = bpy.context.object

        # Fracture the cube into smaller sections
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

        # Remove original cube
        bpy.data.objects.remove(cube, do_unlink=True)

        # Join all fractured parts
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()

        # Clean up geometry
        self.clean_up()

    def clean_up(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add modifiers
        self.add_modifiers(active_obj)

    def add_modifiers(self, obj):
        wireframe_mod = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True

        subsurf_mod = obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = self.smoothness
        subsurf_mod.render_levels = self.smoothness

# Create and generate the model
cell_model = CellularModel(cell_thickness, smoothness_degree)
cell_model.create()
