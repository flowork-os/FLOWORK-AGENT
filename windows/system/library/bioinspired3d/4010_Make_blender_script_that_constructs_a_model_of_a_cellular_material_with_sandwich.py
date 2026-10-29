# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_script_that_constructs_a_model_of_a_cellular_material_with_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender script that constructs a model of a cellular material with sandwich layers. Think step by step.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the sandwich structure
strut_thickness = 0.1  # Thickness of the struts
slab_thickness = 0.4    # Thickness of the top and bottom slabs

class CellularSandwich:
    def __init__(self, strut_thickness, slab_thickness):
        self.strut_thickness = strut_thickness
        self.slab_thickness = slab_thickness

    def create(self):
        self._enable_fracture_cell()
        self._fracture_cube()
        self._add_wireframe()
        self._create_slabs()

    def _enable_fracture_cell(self):
        addon_utils.enable('object_fracture_cell')

    def _fracture_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        initial_cube = bpy.context.active_object
        initial_cube.scale = (1, 1, 0.75)
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
        bpy.data.objects.remove(initial_cube, do_unlink=True)

    def _add_wireframe(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.join()
                break
        active_mesh = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.mode_set(mode='OBJECT')
        wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.strut_thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True
        bpy.ops.object.convert(target='MESH')

    def _create_slabs(self):
        height_of_sandwich = 1.5
        bottom_slab_z = -height_of_sandwich / 2 - self.slab_thickness / 2
        top_slab_z = height_of_sandwich / 2 + self.slab_thickness / 2
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, bottom_slab_z))
        bottom_slab = bpy.context.active_object
        bottom_slab.scale = (1, 1, self.slab_thickness / 2)
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, top_slab_z))
        top_slab = bpy.context.active_object
        top_slab.scale = (1, 1, self.slab_thickness / 2)
        bpy.ops.object.transform_apply(scale=True)

# Create the sandwich
sandwich = CellularSandwich(strut_thickness, slab_thickness)
sandwich.create()
