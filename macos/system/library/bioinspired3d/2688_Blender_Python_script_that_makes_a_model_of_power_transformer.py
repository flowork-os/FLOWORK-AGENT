# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_makes_a_model_of_power_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that makes a model of power transformer

import bpy
import math

# Start with a clean scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model parts
material_dict = {
    'base': bpy.data.materials.new(name='BaseMaterial'),
    'core': bpy.data.materials.new(name='CoreMaterial'),
    'coil': bpy.data.materials.new(name='CoilMaterial'),
    'terminal': bpy.data.materials.new(name='TerminalMaterial')
}
material_dict['base'].diffuse_color = (0.5, 0.5, 0.5, 1)
material_dict['core'].diffuse_color = (0.2, 0.2, 0.2, 1)
material_dict['coil'].diffuse_color = (0.8, 0.8, 0.8, 1)
material_dict['terminal'].diffuse_color = (0.9, 0.9, 0.9, 1)

# Create a base mesh
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_part = bpy.context.object
base_part.name = 'Base'
base_part.scale[2] = 0.1
base_part.data.materials.append(material_dict['base'])

# Create the core mesh
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.5, location=(0, 0, 1.25))
core_part = bpy.context.object
core_part.name = 'Core'
core_part.data.materials.append(material_dict['core'])

# Add coils around the core
for index in range(8):
    phi = index * (math.pi / 4)
    x_pos = 0.6 * math.cos(phi)
    y_pos = 0.6 * math.sin(phi)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.05, location=(x_pos, y_pos, 1.25))
    coil_part = bpy.context.object
    coil_part.name = f'Coil_{index + 1}'
    coil_part.data.materials.append(material_dict['coil'])

# Create terminal components
for i in range(2):
    terminal_x_position = 0.7 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.2, location=(terminal_x_position, 0, 1.5))
    terminal_part = bpy.context.object
    terminal_part.name = f'Terminal_{i + 1}'
    terminal_part.data.materials.append(material_dict['terminal'])


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
