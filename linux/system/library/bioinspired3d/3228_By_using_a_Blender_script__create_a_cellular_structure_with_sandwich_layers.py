# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script__create_a_cellular_structure_with_sandwich_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script, create a cellular structure with sandwich layers

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Constants for the cellular sandwich
strut_width = 0.15
slab_thickness = 0.25

class CellularSandwich:
    def __init__(self, strut_width, slab_thickness):
        self.strut_width = strut_width
        self.slab_thickness = slab_thickness

    def create_structure(self):
        addon_utils.enable('object_fracture_cell')
        self._generate_base_cube()

    def _generate_base_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        self._fracture_cube(cube)

    def _fracture_cube(self, cube):
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
        bpy.data.objects.remove(cube, do_unlink=True)
        self._join_fragments()

    def _join_fragments(self):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()
        self._apply_wireframe()

    def _apply_wireframe(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.mode_set(mode='OBJECT')
        wf_modifier = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wf_modifier.thickness = self.strut_width
        wf_modifier.offset = -1
        wf_modifier.use_even_offset = False
        wf_modifier.use_relative_offset = True
        wf_modifier.use_replace = True
        bpy.ops.object.convert(target='MESH')
        self._create_slabs()

    def _create_slabs(self):
        slab_height = 1.5
        bottom_z = -slab_height / 2 - self.slab_thickness / 2
        top_z = slab_height / 2 + self.slab_thickness / 2
        self._create_slab(bottom_z)
        self._create_slab(top_z)

    def _create_slab(self, z_position):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, self.slab_thickness / 2)
        bpy.ops.object.transform_apply(scale=True)

# Instantiate and create the sandwich
sandwich = CellularSandwich(strut_width, slab_thickness)
sandwich.create_structure()
