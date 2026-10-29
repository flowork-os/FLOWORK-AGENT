# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_build_a_model_of_a_cellular_cube_with_layers_on_top_and_botto" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to build a model of a cellular cube with layers on top and bottom and smoothed think step by step.

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the sandwich structure
thickness_value = 0.25  # Thickness of the struts
smoothness_level = 4  # Level of smoothness
sandwich_thickness = 0.2  # Thickness of the top and bottom slabs

class CellularSandwich:
    def __init__(self, thickness, smoothness, slab_thickness):
        self.thickness = thickness
        self.smoothness = smoothness
        self.slab_thickness = slab_thickness

    def create(self):
        addon_utils.enable('object_fracture_cell')
        self._create_base_cube()
        self._fracture_cube()
        self._join_fragments()
        self._apply_modifiers()
        self._create_sandwich_slabs()

    def _create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        self.base_cube = bpy.context.active_object
        self.base_cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)

    def _fracture_cube(self):
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
            use_remove_original=True
        )
        bpy.data.objects.remove(self.base_cube, do_unlink=True)

    def _join_fragments(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        if bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            bpy.ops.object.join()

    def _apply_modifiers(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Wireframe modifier
        wf_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = self.thickness
        wf_modifier.offset = -1
        bpy.ops.object.convert(target='MESH')

        # Subdivision modifier
        subsurf_modifier = active_obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_modifier.levels = self.smoothness
        subsurf_modifier.render_levels = self.smoothness

    def _create_sandwich_slabs(self):
        slab_height = 1.5
        bottom_z = -slab_height / 2 - self.slab_thickness / 2
        top_z = slab_height / 2 + self.slab_thickness / 2

        # Bottom slab
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_z))
        bottom_slab = bpy.context.active_object
        bottom_slab.scale = (1, 1, self.slab_thickness / 2)
        bpy.ops.object.transform_apply(scale=True)

        # Top slab
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_z))
        top_slab = bpy.context.active_object
        top_slab.scale = (1, 1, self.slab_thickness / 2)
        bpy.ops.object.transform_apply(scale=True)

# Create and build the sandwich
sandwich = CellularSandwich(thickness_value, smoothness_level, sandwich_thickness)
sandwich.create()
