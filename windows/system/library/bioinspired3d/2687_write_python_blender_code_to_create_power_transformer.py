# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_to_create_power_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code to create power transformer.

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for various components
base_mat = bpy.data.materials.new(name='MainBodyMaterial')
base_mat.diffuse_color = (0.5, 0.5, 0.5, 1)

core_mat = bpy.data.materials.new(name='InnerCoreMaterial')
core_mat.diffuse_color = (0.2, 0.2, 0.2, 1)

coil_mat = bpy.data.materials.new(name='SpiralMaterial')
coil_mat.diffuse_color = (0.8, 0.8, 0.8, 1)

terminal_mat = bpy.data.materials.new(name='EndCapMaterial')
terminal_mat.diffuse_color = (0.9, 0.9, 0.9, 1)

# Create the base mesh
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_mesh = bpy.context.object
base_mesh.name = 'Base'
base_mesh.scale[2] = 0.1
base_mesh.data.materials.append(base_mat)

# Add the core mesh
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.5, location=(0, 0, 1.25))
core_mesh = bpy.context.object
core_mesh.name = 'Core'
core_mesh.data.materials.append(core_mat)

# Generate coils in a circular arrangement
for i in range(8):
    angle_offset = i * (math.pi / 4)
    coil_x = 0.6 * math.cos(angle_offset)
    coil_y = 0.6 * math.sin(angle_offset)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.05, location=(coil_x, coil_y, 1.25))
    coil_mesh = bpy.context.object
    coil_mesh.name = f'Coil_{i + 1}'
    coil_mesh.data.materials.append(coil_mat)

# Create terminal pieces
for j in range(2):
    terminal_pos = 0.7 * (j * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.2, location=(terminal_pos, 0, 1.5))
    terminal_mesh = bpy.context.object
    terminal_mesh.name = f'Terminal_{j + 1}'
    terminal_mesh.data.materials.append(terminal_mat)


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
