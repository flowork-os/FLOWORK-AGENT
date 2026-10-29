# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code__make_logo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code, make logo.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the gears
gear_material_instance = bpy.data.materials.new(name="Steel Color")
gear_material_instance.diffuse_color = (0.7, 0.7, 0.7, 1)  # Lighter steel color

# Function to add a gear
def add_gear(position, gear_name):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.2, location=position)
    new_gear = bpy.context.object
    new_gear.name = gear_name
    new_gear.data.materials.append(gear_material_instance)

# Create gears in the scene
add_gear((0, 0, 0), "Main Gear")
add_gear((1.5, 0, 0), "Secondary Gear")
add_gear((0.75, 1.3, 0), "Tertiary Gear")


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
