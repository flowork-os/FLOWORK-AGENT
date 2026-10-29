# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_makes_a_model_of_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that makes a model of birthday cake

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for cake components
cake_mat = bpy.data.materials.new(name="Cake Material")
cake_mat.diffuse_color = (0.8, 0.6, 0.4, 1)
frosting_mat = bpy.data.materials.new(name="Frosting Material")
frosting_mat.diffuse_color = (1, 0.8, 0.8, 1)
candle_mat = bpy.data.materials.new(name="Candle Material")
candle_mat.diffuse_color = (1, 0, 0, 1)

# Function to create a cylinder with a material

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Constructing the cake tiers
bottom_tier = create_cylinder(1, 0.5, (0, 0, 0.25), "Bottom Tier", cake_mat)
top_tier = create_cylinder(0.75, 0.5, (0, 0, 0.75), "Top Tier", cake_mat)

# Adding frosting layers
bottom_frosting = create_cylinder(1.05, 0.1, (0, 0, 0.3), "Bottom Frosting", frosting_mat)
top_frosting = create_cylinder(0.85, 0.1, (0, 0, 0.85), "Top Frosting", frosting_mat)

# Create candles using a loop
for i in range(8):
    theta = i * (2 * math.pi / 8)
    x_pos = 0.6 * math.cos(theta)
    y_pos = 0.6 * math.sin(theta)
    candle = create_cylinder(0.05, 0.3, (x_pos, y_pos, 1.1), f"Candle {i + 1}", candle_mat)


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
