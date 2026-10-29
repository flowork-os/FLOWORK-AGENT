# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_mandala_pattern_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create mandala pattern using Blender code

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mandala_material = bpy.data.materials.new(name="Mandala Material")
mandala_material.diffuse_color = (0.5, 0.5, 0.5, 1)

bpy.ops.mesh.primitive_circle_add(radius=1, location=(0, 0, 0))
center_circle = bpy.context.object
center_circle.name = "Center Circle"
center_circle.data.materials.append(mandala_material)

def add_radiating_shapes(total_shapes):
    angle_increment = 2 * math.pi / total_shapes
    for i in range(total_shapes):
        angle = i * angle_increment
        x = math.cos(angle) * 2
        y = math.sin(angle) * 2
        bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.1, location=(x, y, 0), rotation=(0, 0, angle))
        shape = bpy.context.object
        shape.name = f"Radiating Shape {i + 1}"
        shape.data.materials.append(mandala_material)

def add_torus_layers(num_layers):
    for layer in range(1, num_layers + 1):
        radius = 2 + layer
        add_radiating_shapes(12)

add_radiating_shapes(12)
add_torus_layers(3)


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
