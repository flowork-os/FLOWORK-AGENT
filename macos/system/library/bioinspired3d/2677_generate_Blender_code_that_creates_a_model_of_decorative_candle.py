# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_creates_a_model_of_decorative_candle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that creates a model of decorative candle

import bpy

# Deselect all objects and remove existing meshes
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a function to generate a cylinder

def generate_cylinder(radius, height, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    current_object = bpy.context.object
    current_object.name = name
    return current_object

# Create the main components of the candle
candle = generate_cylinder(0.3, 1.5, (0, 0, 0.75), 'Candle')
wick = generate_cylinder(0.02, 0.2, (0, 0, 1.6), 'Wick')
holder_base = generate_cylinder(0.4, 0.1, (0, 0, 0.05), 'Holder Base')
holder_top = generate_cylinder(0.35, 0.1, (0, 0, 0.1), 'Holder Top')

# Function to create and assign materials to objects

def assign_material(object, mat_name, mat_color):
    material = bpy.data.materials.new(name=mat_name)
    material.diffuse_color = mat_color
    object.data.materials.append(material)

# Define colors for each part
candle_color = (1, 0.85, 0.7, 1)
wick_color = (0.1, 0.1, 0.1, 1)
holder_color = (0.5, 0.5, 0.5, 1)

# Apply materials to the candle, wick, and holder
assign_material(candle, 'Candle Material', candle_color)
assign_material(wick, 'Wick Material', wick_color)
assign_material(holder_base, 'Holder Material', holder_color)
assign_material(holder_top, 'Holder Material', holder_color)


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
