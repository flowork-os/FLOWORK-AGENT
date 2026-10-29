# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_generates_a_cellular_material_with_sandwich_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that generates a cellular material with sandwich layers.

import bpy
import addon_utils

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the sandwich structure
strut_thickness = 0.15  # Thickness of the struts
slab_size = 0.35  # Thickness of the top and bottom slabs

class SandwichMaker:
    def __init__(self, strut_thickness, slab_size):
        self.strut_thickness = strut_thickness
        self.slab_size = slab_size

    def create(self):
        addon_utils.enable('object_fracture_cell')
        self.create_base_cube()
        self.create_slab(-0.75 - self.slab_size / 2)
        self.create_slab(0.75 + self.slab_size / 2)

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add()
        base_cube = bpy.context.active_object
        base_cube.scale = (1, 1, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        self.fracture_cube(base_cube)

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
            use_remove_original=True
        )
        bpy.data.objects.remove(cube, do_unlink=True)
        self.join_fragments()

    def join_fragments(self):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()
        self.clean_mesh()

    def clean_mesh(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.apply_wireframe(active_obj)

    def apply_wireframe(self, obj):
        wire_mod = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wire_mod.thickness = self.strut_thickness
        wire_mod.offset = -1
        bpy.ops.object.convert(target='MESH')

    def create_slab(self, z_position):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        slab = bpy.context.active_object
        slab.scale = (1, 1, self.slab_size / 2)
        bpy.ops.object.transform_apply(scale=True)

# Instantiate and create the sandwich structure
sandwich_maker = SandwichMaker(strut_thickness, slab_size)
sandwich_maker.create()
