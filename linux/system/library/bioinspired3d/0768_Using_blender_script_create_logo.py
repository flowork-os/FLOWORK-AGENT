# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_script_create_logo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender script create logo.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the gears
material_gray = bpy.data.materials.new(name="Gray Gear Material")
material_gray.diffuse_color = (0.6, 0.6, 0.6, 1)  # Slightly lighter gray

# Function to create a gear

def create_gear(location, name):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.2, location=location)
    gear = bpy.context.object
    gear.name = name
    gear.data.materials.append(material_gray)

# Generate gears at specified locations
create_gear((0, 0, 0), "Gear A")
create_gear((1.5, 0, 0), "Gear B")
create_gear((0.75, 1.3, 0), "Gear C")


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
