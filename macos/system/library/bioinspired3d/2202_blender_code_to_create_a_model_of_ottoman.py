# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_create_a_model_of_ottoman" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to create a model of ottoman.

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the ottoman color
material_color = bpy.data.materials.new(name="Ottoman Color")
material_color.diffuse_color = (0.55, 0.28, 0.12, 1)  # A medium brown color

# Function to create an ottoman base
def add_ottoman_base():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.25))
    base = bpy.context.object
    base.name = "Ottoman Base"
    base.scale = (1, 1, 0.24)
    base.data.materials.append(material_color)
    return base

# Function to create a leg
def add_leg(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.2, location=(x, y, 0.1))
    leg = bpy.context.object
    leg.data.materials.append(material_color)
    return leg

# Create the ottoman base
ottoman_base = add_ottoman_base()

# Create the legs at calculated positions
positions = [(0.4, 0.4), (0.4, -0.4), (-0.4, 0.4), (-0.4, -0.4)]
for index, (x, y) in enumerate(positions):
    leg = add_leg(x, y)
    leg.name = f"Leg {index + 1}"


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
