# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_create_a_model_of_a_cellular_structure_with_sandwich_top" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script create a model of a cellular structure with sandwich top and bottom layers and with smooth curves. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_width = 0.1
smooth_level = 5
sandwich_thickness = 0.4

class CellularSandwich:
    def __init__(self, thickness, smoothness, size):
        self.thickness = thickness
        self.smoothness = smoothness
        self.size = size

    def create(self):
        addon_utils.enable("object_fracture_cell")
        self.build_cube()
        self.fracture_cube()
        self.join_fragments()
        self.add_modifiers()
        self.create_slabs()

    def build_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        self.cube = bpy.context.active_object
        self.cube.scale = (1, 1, 0.75)
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
            use_remove_original=True,
            collection_name="",
            use_debug_points=False,
            use_debug_redraw=True,
            use_debug_bool=False
        )
        bpy.data.objects.remove(self.cube, do_unlink=True)

    def join_fragments(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
        bpy.ops.object.join()

    def add_modifiers(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.mode_set(mode='OBJECT')
        wireframe_mod = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')
        subsurf_mod = active_obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = self.smoothness
        subsurf_mod.render_levels = self.smoothness

    def create_slabs(self):
        height = 1.5
        bottom_z = -height / 2 - self.size / 2
        top_z = height / 2 + self.size / 2
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_z))
        bottom_slab = bpy.context.active_object
        bottom_slab.scale = (1, 1, self.size / 2)
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_z))
        top_slab = bpy.context.active_object
        top_slab.scale = (1, 1, self.size / 2)
        bpy.ops.object.transform_apply(scale=True)

sandwich = CellularSandwich(strut_width, smooth_level, sandwich_thickness)
sandwich.create()
