# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_builds_a_cellular_cube_with_smooth_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that builds a cellular cube with smooth edges.

import bpy
import addon_utils

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the cellular model
cell_thickness = 0.15
smooth_levels = 4

class CellularModel:
    @staticmethod
    def create():
        # Method to create a smoothed cellular structure.
        # Process:
        # 1. Add a cube.
        # 2. Fracture and merge the cube.
        # 3. Apply wireframe modifier for cellular look.
        # 4. Smooth edges with a subsurface modifier.

        # Enable the Fracture Cell add-on
        addon_utils.enable('object_fracture_cell')

        # Create the initial cube
        bpy.ops.mesh.primitive_cube_add(size=2)
        cube_obj = bpy.context.object

        # Fracture the cube
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

        # Remove the original cube
        if cube_obj and cube_obj.name in bpy.data.objects:
            bpy.data.objects.remove(cube_obj, do_unlink=True)

        # Join fractured pieces
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

        if bpy.context.selected_objects and bpy.context.view_layer.objects.active:
            active_mesh = bpy.context.view_layer.objects.active
            # Clean geometry
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.2)
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.mesh.dissolve_limited(angle_limit=1)
            bpy.ops.object.mode_set(mode='OBJECT')

            # Wireframe Modifier
            wireframe_mod = active_mesh.modifiers.new(name='Wireframe', type='WIREFRAME')
            wireframe_mod.thickness = cell_thickness
            wireframe_mod.offset = -1
            wireframe_mod.use_even_offset = False
            wireframe_mod.use_relative_offset = True
            wireframe_mod.use_replace = True

            # Subsurface Modifier
            subsurf_mod = active_mesh.modifiers.new(name='Subdivision', type='SUBSURF')
            subsurf_mod.levels = smooth_levels
            subsurf_mod.render_levels = smooth_levels

# Execute the creation of the cellular model
CellularModel.create()
