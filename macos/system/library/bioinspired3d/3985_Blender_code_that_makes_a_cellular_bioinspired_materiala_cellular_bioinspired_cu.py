# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_makes_a_cellular_bioinspired_materiala_cellular_bioinspired_cu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that makes a cellular bioinspired materiala cellular bioinspired cubea cellular bioinspired structure with layers on top and bottom. Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_thickness = 0.15  # Thickness of the struts
slab_thickness = 0.25  # Thickness of the top and bottom slabs

class CellularSandwich:
    def __init__(self, thickness, size):
        self.thickness = thickness
        self.size = size
        self.sandwich_height = 1.5

    def create(self):
        self.activate_fracture_addon()
        cube = self.create_base_cube()
        self.fracture_cube(cube)
        self.join_fragments()
        self.apply_wireframe_modifier()
        self.add_sandwich_slabs()

    def activate_fracture_addon(self):
        addon_utils.enable('object_fracture_cell')

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        return cube

    def fracture_cube(self, cube):
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
            collection_name='',
            use_debug_points=False,
            use_debug_redraw=True,
            use_debug_bool=False
        )
        bpy.data.objects.remove(cube, do_unlink=True)

    def join_fragments(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()

    def apply_wireframe_modifier(self):
        if bpy.context.view_layer.objects.active.type == 'MESH':
            active_obj = bpy.context.view_layer.objects.active
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.2)
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.mesh.dissolve_limited(angle_limit=1)
            bpy.ops.object.mode_set(mode='OBJECT')
            wireframe = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
            wireframe.thickness = self.thickness
            wireframe.offset = -1
            wireframe.use_even_offset = False
            wireframe.use_relative_offset = True
            wireframe.use_replace = True
            bpy.ops.object.convert(target='MESH')

    def add_sandwich_slabs(self):
        bottom_z = -self.sandwich_height / 2 - self.size / 2
        top_z = self.sandwich_height / 2 + self.size / 2
        self.create_slab(bottom_z)
        self.create_slab(top_z)

    def create_slab(self, z_position):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, self.size / 2)
        bpy.ops.object.transform_apply(scale=True)

sandwich = CellularSandwich(strut_thickness, slab_thickness)
sandwich.create()
