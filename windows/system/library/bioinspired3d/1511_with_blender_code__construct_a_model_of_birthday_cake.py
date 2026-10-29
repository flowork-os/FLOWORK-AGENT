# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code__construct_a_model_of_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code, construct a model of birthday cake

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material setup
material_cake = bpy.data.materials.new(name="Cake")
material_cake.diffuse_color = (0.8, 0.6, 0.4, 1)
material_frosting = bpy.data.materials.new(name="Frosting")
material_frosting.diffuse_color = (1, 0.8, 0.8, 1)
material_candle = bpy.data.materials.new(name="Candle")
material_candle.diffuse_color = (1, 0, 0, 1)

# Create cake tiers and frosting
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
bottom_cake = bpy.context.object
bottom_cake.name = "Cake Base"
bottom_cake.data.materials.append(material_cake)

bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.5, location=(0, 0, 0.75))
top_cake = bpy.context.object
top_cake.name = "Cake Top"
top_cake.data.materials.append(material_cake)

# Add frosting to the tiers
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 0.3))
bottom_frosting_layer = bpy.context.object
bottom_frosting_layer.name = "Frosting Base"
bottom_frosting_layer.data.materials.append(material_frosting)

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 0.85))
top_frosting_layer = bpy.context.object
top_frosting_layer.name = "Frosting Top"
top_frosting_layer.data.materials.append(material_frosting)

# Place candles around the top tier
for j in range(8):
    candle_position = j * (2 * math.pi / 8)
    candle_x_pos = 0.6 * math.cos(candle_position)
    candle_y_pos = 0.6 * math.sin(candle_position)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3, location=(candle_x_pos, candle_y_pos, 1.1))
    candle_object = bpy.context.object
    candle_object.name = f"Candle {j + 1}"
    candle_object.data.materials.append(material_candle)


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
