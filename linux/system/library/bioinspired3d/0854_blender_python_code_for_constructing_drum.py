# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_constructing_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for constructing drum.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different parts of the drum
material_for_body = bpy.data.materials.new(name='Drum Body')
material_for_body.diffuse_color = (0.8, 0.2, 0.2, 1)
material_for_head = bpy.data.materials.new(name='Drumhead')
material_for_head.diffuse_color = (0.9, 0.9, 0.9, 1)
material_for_rods = bpy.data.materials.new(name='Tension Rods')
material_for_rods.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the drum components
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
drum_body = bpy.context.object
bpy.context.object.name = 'Drum Body'
drum_body.data.materials.append(material_for_body)

bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.55))
drum_head = bpy.context.object
bpy.context.object.name = 'Drumhead'
drum_head.data.materials.append(material_for_head)

# Create tension rods in a loop
for index in range(8):
    angle_rad = index * (2 * math.pi / 8)
    x_coord = 1.05 * math.cos(angle_rad)
    y_coord = 1.05 * math.sin(angle_rad)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.6, location=(x_coord, y_coord, 0.8))
    tension_rod = bpy.context.object
    tension_rod.name = f'Tension Rod {index + 1}'
    tension_rod.data.materials.append(material_for_rods)


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
