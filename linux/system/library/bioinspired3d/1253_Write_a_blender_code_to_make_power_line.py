# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_to_make_power_line" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code to make power line

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material with a gray color
material = bpy.data.materials.new(name="Gray")
material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to generate the pole and crossbar

def construct_structure():
    # Add the pole
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=5, location=(0, 0, 2.5))
    pole = bpy.context.object
    pole.name = "Pole"
    pole.data.materials.append(material)
    
    # Add the crossbar
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(0, 0, 4.5), rotation=(1.5708, 0, 0))
    crossbar = bpy.context.object
    crossbar.name = "Crossbar"
    crossbar.data.materials.append(material)

    # Add power lines
    for i in range(3):
        y_offset = 0.5 * (i - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=5, location=(0, y_offset, 4.5), rotation=(0, 1.5708, 0))
        line = bpy.context.object
        line.name = f"PowerLine_{i + 1}"
        line.data.materials.append(material)

# Execute the construction
construct_structure()


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
