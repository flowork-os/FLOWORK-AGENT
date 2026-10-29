# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code_generate_a_cellular_material_with_smooth_curves_and_with_sand" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code generate a cellular material with smooth curves and with sandwich top and bottom layers. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cell_thickness = 0.25
smoothing_level = 4
slab_height = 0.3

class SandwichBuilder:
    def __init__(self, thickness, smoothness, size):
        self.thickness = thickness
        self.smoothness = smoothness
        self.size = size

    def create_structure(self):
        addon_utils.enable('object_fracture_cell')
        self.create_base_cube()
        self.fracture_cube()
        self.combine_fragments()
        self.apply_modifiers()
        self.add_sandwich_slabs()

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        self.base_cube = bpy.context.active_object
        self.base_cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)

    def fracture_cube(self):
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

    def combine_fragments(self):
        bpy.data.objects.remove(self.base_cube, do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()

    def apply_modifiers(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.mode_set(mode='OBJECT')

        wire_mod = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wire_mod.thickness = self.thickness
        wire_mod.offset = -1
        wire_mod.use_relative_offset = True
        bpy.ops.object.convert(target='MESH')

        sub_mod = active_obj.modifiers.new(name='Subdivision', type='SUBSURF')
        sub_mod.levels = self.smoothness
        sub_mod.render_levels = self.smoothness

    def add_sandwich_slabs(self):
        slab_positions = [-0.75 - self.size / 2, 0.75 + self.size / 2]
        for pos in slab_positions:
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, pos))
            slab = bpy.context.active_object
            slab.scale = (1, 1, self.size / 2)
            bpy.ops.object.transform_apply(scale=True)

builder = SandwichBuilder(cell_thickness, smoothing_level, slab_height)
builder.create_structure()
