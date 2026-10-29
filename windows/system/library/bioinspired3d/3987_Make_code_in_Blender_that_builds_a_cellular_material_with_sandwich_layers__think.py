# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_code_in_Blender_that_builds_a_cellular_material_with_sandwich_layers__think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make code in Blender that builds a cellular material with sandwich layers. think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

strut_width = 0.25  # Thickness of the struts
slab_thickness = 0.35  # Thickness of the top and bottom slabs

class SandwichCreator:
    def __init__(self, strut_width, slab_thickness):
        self.struts = strut_width
        self.slab = slab_thickness

    def create_sandwich(self):
        self.enable_fracture_addon()
        cube = self.create_cube()
        self.fracture(cube)
        self.join_meshes()
        self.add_wireframe()
        self.create_slabs()

    def enable_fracture_addon(self):
        addon_utils.enable('object_fracture_cell')

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        return cube

    def fracture(self, cube):
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

    def join_meshes(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()

    def add_wireframe(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        wireframe_mod = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.struts
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    def create_slabs(self):
        slab_height = 1.5
        bottom_z = -slab_height / 2 - self.slab / 2
        top_z = slab_height / 2 + self.slab / 2
        self.create_slab(bottom_z)
        self.create_slab(top_z)

    def create_slab(self, z_position):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, self.slab / 2)
        bpy.ops.object.transform_apply(scale=True)

sandwich_maker = SandwichCreator(strut_width, slab_thickness)
sandwich_maker.create_sandwich()
