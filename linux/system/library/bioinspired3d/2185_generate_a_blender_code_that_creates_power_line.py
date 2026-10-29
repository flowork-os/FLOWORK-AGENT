# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_that_creates_power_line" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code that creates power line.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the structure
material_gray = bpy.data.materials.new(name="MaterialGray")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, rotation, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_gray)
    return obj

# Create the main pole
create_cylinder(0.1, 5, (0, 0, 2.5), (0, 0, 0), "MainPole")

# Create the crossbar
create_cylinder(0.05, 1.5, (0, 0, 4.5), (1.5708, 0, 0), "Crossbar")

# Create power lines using a loop
for index in range(3):
    y_position = 0.5 * (index - 1)
    create_cylinder(0.01, 5, (0, y_position, 4.5), (0, 1.5708, 0), f"PowerLine_{index + 1}")


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
