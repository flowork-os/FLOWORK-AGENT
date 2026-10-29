# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_cellular_cube_with_sandwich_layers_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a cellular cube with sandwich layers in a blender code

import bpy
import addon_utils

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for sandwich structure
strut_width = 0.25
slab_height = 0.3

class CellularSandwich:
    def __init__(self, thickness, size):
        self.thickness = thickness
        self.size = size

    def create_sandwich(self):
        addon_utils.enable('object_fracture_cell')
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)

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
        self.join_fragments()
        self.apply_wireframe_modifier()
        self.create_slabs()

    def join_fragments(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        if bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            bpy.ops.object.join()

    def apply_wireframe_modifier(self):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.2)
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.mesh.dissolve_limited(angle_limit=1)
            bpy.ops.object.mode_set(mode='OBJECT')

            wf_mod = active_obj.modifiers.new(name='Wireframe', type='WIREFRAME')
            wf_mod.thickness = self.thickness
            wf_mod.offset = -1
            wf_mod.use_even_offset = False
            wf_mod.use_relative_offset = True
            wf_mod.use_replace = True
            bpy.ops.object.convert(target='MESH')

    def create_slabs(self):
        slab_z_bottom = -0.75 - self.size / 2
        slab_z_top = 0.75 + self.size / 2
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, slab_z_bottom))
        bottom_slab = bpy.context.active_object
        bottom_slab.scale = (1, 1, self.size / 2)
        bpy.ops.object.transform_apply(scale=True)

        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, slab_z_top))
        top_slab = bpy.context.active_object
        top_slab.scale = (1, 1, self.size / 2)
        bpy.ops.object.transform_apply(scale=True)

# Instantiate and create the cellular sandwich
sandwich = CellularSandwich(strut_width, slab_height)
sandwich.create_sandwich()
