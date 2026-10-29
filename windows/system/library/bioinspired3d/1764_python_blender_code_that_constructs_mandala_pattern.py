# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_constructs_mandala_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that constructs mandala pattern

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

gray_material = bpy.data.materials.new(name="Gray Material")
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Medium gray

bpy.ops.mesh.primitive_circle_add(radius=1, location=(0, 0, 0))
main_circle = bpy.context.object
main_circle.name = "Main Circle"
main_circle.data.materials.append(gray_material)

shape_count = 12
angle_increment = 2 * math.pi / shape_count

for index in range(shape_count):
    current_angle = index * angle_increment
    x_position = math.cos(current_angle) * 2
    y_position = math.sin(current_angle) * 2
    bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.1, location=(x_position, y_position, 0), rotation=(0, 0, current_angle))
    cone = bpy.context.object
    cone.name = f"Cone {index + 1}"
    cone.data.materials.append(gray_material)

for layer_index in range(1, 4):
    layer_radius = 2 + layer_index
    for index in range(shape_count):
        current_angle = index * angle_increment
        x_position = math.cos(current_angle) * layer_radius
        y_position = math.sin(current_angle) * layer_radius
        bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(x_position, y_position, 0), rotation=(0, 0, current_angle))
        torus_shape = bpy.context.object
        torus_shape.name = f"Torus Layer {layer_index} Cone {index + 1}"
        torus_shape.data.materials.append(gray_material)


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
