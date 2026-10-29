# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_birthday_cake_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of birthday cake using code in Blender

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for cake and decorations
cake_material = bpy.data.materials.new(name="Cake Color")
cake_material.diffuse_color = (0.8, 0.6, 0.4, 1)
frosting_material = bpy.data.materials.new(name="Frosting Color")
frosting_material.diffuse_color = (1, 0.8, 0.8, 1)
candle_material = bpy.data.materials.new(name="Candle Color")
candle_material.diffuse_color = (1, 0, 0, 1)

# Function to add a cylinder
def add_cylinder(radius, height, position, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)

# Build the cake tiers
add_cylinder(1, 0.5, (0, 0, 0.25), "Base Tier", cake_material)
add_cylinder(0.75, 0.5, (0, 0, 0.75), "Upper Tier", cake_material)

# Create frosting
add_cylinder(1.05, 0.1, (0, 0, 0.3), "Base Frosting", frosting_material)
add_cylinder(0.85, 0.1, (0, 0, 0.85), "Upper Frosting", frosting_material)

# Generate candles
for i in range(8):
    candle_angle = i * (2 * math.pi / 8)
    candle_x = 0.6 * math.cos(candle_angle)
    candle_y = 0.6 * math.sin(candle_angle)
    add_cylinder(0.05, 0.3, (candle_x, candle_y, 1.1), f"Candle_{i + 1}", candle_material)


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
