# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_creating_pen_holder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for creating pen holder

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a gray material
new_material = bpy.data.materials.new(name="GrayMaterial")
new_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to generate a cylinder

def add_cylinder(rad, depth, loc, obj_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(new_material)
    return obj

# Add base
base_cylinder = add_cylinder(1.5, 0.1, (0, 0, 0), "Base")

# Create the main compartment
main_cylinder = add_cylinder(1, 2, (0, 0, 1.05), "MainCompartment")

# Define positions for smaller compartments
smaller_positions = [(1, 1, 0.8), (-1, 1, 0.8), (1, -1, 0.8), (-1, -1, 0.8)]
for index, position in enumerate(smaller_positions, start=1):
    add_cylinder(0.5, 1.5, position, f"Compartment_{index}")


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
