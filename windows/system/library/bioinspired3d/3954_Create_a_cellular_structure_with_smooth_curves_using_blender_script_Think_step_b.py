# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_cellular_structure_with_smooth_curves_using_blender_script_Think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a cellular structure with smooth curves using blender script Think step by step

import bpy
import addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the cellular model
strut_width = 0.1  # Width of the struts
smooth_level = 2  # Level of subdivision smoothing

class FracturedCell:
    def __init__(self, width, smooth):
        self.width = width
        self.smooth = smooth

    def create_structure(self):
        addon_utils.enable("object_fracture_cell")
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube = bpy.context.object

        # Perform fracturing operation
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

        # Clean up by removing the original cube
        bpy.data.objects.remove(cube, do_unlink=True)

        # Join all fractured pieces together
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()

        # Finalize geometry cleanup
        self.finalize_cleanup()

    def finalize_cleanup(self):
        active_obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.2)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.mesh.dissolve_limited(angle_limit=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Wireframe and Subdivision modifiers
        self.add_modifiers(active_obj)

    def add_modifiers(self, obj):
        wireframe_mod = obj.modifiers.new(name='Wireframe', type='WIREFRAME')
        wireframe_mod.thickness = self.width
        wireframe_mod.offset = -1
        wireframe_mod.use_even_offset = False
        wireframe_mod.use_relative_offset = True
        wireframe_mod.use_replace = True

        subsurf_mod = obj.modifiers.new(name='Subdivision', type='SUBSURF')
        subsurf_mod.levels = self.smooth
        subsurf_mod.render_levels = self.smooth

# Create and build the fractured cell model
fractured_cell = FracturedCell(strut_width, smooth_level)
fractured_cell.create_structure()
