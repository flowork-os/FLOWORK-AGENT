# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_generating_a_model_of_power_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for generating a model of power transformer.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts of the model
mat_core = bpy.data.materials.new(name='CoreMaterial')
mat_core.diffuse_color = (0.4, 0.4, 0.4, 1)  # Slightly darker gray
mat_coil = bpy.data.materials.new(name='CoilMaterial')
mat_coil.diffuse_color = (1, 0.3, 0, 1)  # Darker orange
mat_terminal = bpy.data.materials.new(name='TerminalMaterial')
mat_terminal.diffuse_color = (0, 0, 0, 1)  # Black for terminals

# Create the core cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=2, location=(0, 0, 0))
core_obj = bpy.context.object
core_obj.name = 'Core'
core_obj.data.materials.append(mat_core)

# Create coils using a loop
for index in range(2):
    coil_z = 0.5 * (index * 2 - 1)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.05, location=(0, 0, coil_z))
    coil_obj = bpy.context.object
    coil_obj.name = f'Coil_{index + 1}'
    coil_obj.data.materials.append(mat_coil)

# Create terminals
for index in range(2):
    terminal_x = 0.2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.2, location=(terminal_x, 0, 1.1))
    terminal_obj = bpy.context.object
    terminal_obj.name = f'Terminal_{index + 1}'
    terminal_obj.data.materials.append(mat_terminal)


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
