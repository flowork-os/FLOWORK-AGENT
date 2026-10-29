# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_construct_a_cellular_structure_smoothed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to construct a cellular structure smoothed

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the cellular model
cell_thickness = 0.15  # Thickness of the struts
smooth_level = 4        # Level of smoothness

class CellularStructure:
    def __init__(self, thickness, smoothness):
        self.thickness = thickness
        self.smoothness = smoothness

    def create(self):
        # Enable the required add-on
        addon_utils.enable('object_fracture_cell')
        # Add a cube as a base
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube = bpy.context.object
        # Execute the fracture operation
        self.fracture_cube(cube)

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
        self.join_fragments()

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
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2) 
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.apply_modifiers(active_obj)

    def apply_modifiers(self, obj):
        wireframe_mod = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.thickness
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True

        subsurf_mod = obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = self.smoothness
        subsurf_mod.render_levels = self.smoothness

# Instantiate and create the cellular structure
cell_structure = CellularStructure(cell_thickness, smooth_level)
cell_structure.create()
