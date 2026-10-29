# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_creates_a_model_of_mandala_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that creates a model of mandala design

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material properties
mat_red = bpy.data.materials.new(name='Red')
mat_red.diffuse_color = (0.8, 0.2, 0.2, 1)
mat_green = bpy.data.materials.new(name='Green')
mat_green.diffuse_color = (0.2, 0.8, 0.2, 1)
mat_blue = bpy.data.materials.new(name='Blue')
mat_blue.diffuse_color = (0.2, 0.2, 0.8, 1)

# Create the central shape
bpy.ops.mesh.primitive_circle_add(radius=1, location=(0, 0, 0))
central_shape = bpy.context.object
central_shape.name = 'Core'
central_shape.data.materials.append(mat_red)

# Generate the surrounding circles
for idx in range(1, 4):
    bpy.ops.mesh.primitive_circle_add(radius=1 + idx, location=(0, 0, 0))
    outer_circle = bpy.context.object
    outer_circle.name = f'Circle {idx}'
    outer_circle.data.materials.append(mat_green if idx % 2 == 0 else mat_blue)

# Create petal shapes
num_petals = 12
for j in range(num_petals):
    petal_angle = j * (2 * math.pi / num_petals)
    x_coord = (1.5 + 0.5) * math.cos(petal_angle)
    y_coord = (1.5 + 0.5) * math.sin(petal_angle)
    bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.5, location=(x_coord, y_coord, 0), rotation=(0, 0, petal_angle))
    petal_shape = bpy.context.object
    petal_shape.name = f'Petal {j + 1}'
    petal_shape.data.materials.append(mat_red)

# Create radial lines
for k in range(24):
    line_angle = k * (2 * math.pi / 24)
    x_line = 3 * math.cos(line_angle)
    y_line = 3 * math.sin(line_angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3, location=(x_line / 2, y_line / 2, 0), rotation=(0, 0, line_angle))
    line_shape = bpy.context.object
    line_shape.name = f'Line {k + 1}'
    line_shape.data.materials.append(mat_blue)


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
