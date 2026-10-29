# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_python_code_make_a_cellular_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender python code make a cellular structure.

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the thickness for the wireframe
wire_thickness = 0.2

class CellularStructure:
    def __init__(self, thickness):
        self.thickness = thickness

    def create(self):
        addon_utils.enable("object_fracture_cell")
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube = bpy.context.object
        self.fracture_cube(cube)
        self.join_fragments()

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
            collection_name="",
            use_debug_points=False,
            use_debug_redraw=True,
            use_debug_bool=False
        )
        if cube and cube.name in bpy.data.objects:
            bpy.data.objects.remove(cube, do_unlink=True)

    def join_fragments(self):
        bpy.ops.object.select_all(action='DESELECT')
        first_mesh = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
                if first_mesh is None:
                    first_mesh = obj
        if first_mesh:
            bpy.context.view_layer.objects.active = first_mesh
            bpy.ops.object.join()
            self.clean_geometry()

    def clean_geometry(self):
        if bpy.context.selected_objects:
            active_obj = bpy.context.view_layer.objects.active
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.2)
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.mesh.dissolve_limited(angle_limit=1)
            bpy.ops.object.mode_set(mode='OBJECT')
            self.apply_wireframe(active_obj)

    def apply_wireframe(self, obj):
        wireframe_mod = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True

# Create the cellular structure
cell_structure = CellularStructure(wire_thickness)
cell_structure.create()
