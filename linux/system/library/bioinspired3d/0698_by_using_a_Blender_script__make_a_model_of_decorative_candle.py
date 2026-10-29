# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__make_a_model_of_decorative_candle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, make a model of decorative candle

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder with specified parameters

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the candle with a specified height and radius
candle = create_cylinder(radius=0.3, depth=1.5, location=(0, 0, 0.75), name='Candle')

# Create the wick above the candle
wick = create_cylinder(radius=0.02, depth=0.2, location=(0, 0, 1.6), name='Wick')

# Create the holder base
holder_base = create_cylinder(radius=0.4, depth=0.1, location=(0, 0, 0.05), name='Holder Base')
# Create the holder top
holder_top = create_cylinder(radius=0.35, depth=0.1, location=(0, 0, 0.1), name='Holder Top')

# Function to create and assign a material

def add_material(obj, name, color):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    obj.data.materials.append(material)

# Assign materials to the candle, wick, and holder
add_material(candle, 'Candle Material', (1, 0.85, 0.7, 1))
add_material(wick, 'Wick Material', (0.1, 0.1, 0.1, 1))
add_material(holder_base, 'Holder Material', (0.5, 0.5, 0.5, 1))
add_material(holder_top, 'Holder Material', (0.5, 0.5, 0.5, 1))


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
