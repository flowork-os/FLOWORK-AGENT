# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_generate_basketball" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to generate basketball

import bpy

# Start by clearing all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define basketball colors
basketball_color = (1.0, 0.55, 0.0, 1)
line_color = (0, 0, 0, 1)

# Create materials for the basketball and lines
basketball_material = bpy.data.materials.new(name='BasketballColor')
basketball_material.diffuse_color = basketball_color
line_material = bpy.data.materials.new(name='LineColor')
line_material.diffuse_color = line_color

# Create the basketball object
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
basketball_obj = bpy.context.object
basketball_obj.name = 'Basketball'
basketball_obj.data.materials.append(basketball_material)

# Function to add lines

def add_line(rotation, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=1.01, depth=0.05, location=(0, 0, 0), rotation=rotation)
    line = bpy.context.object
    line.name = name
    line.data.materials.append(line_material)

# Add the lines with specified rotations
add_line((1.5708, 0, 0), 'Horizontal Line')
add_line((0, 1.5708, 0), 'Vertical Line')
add_line((0.7854, 0, 0), 'Diagonal Line 1')
add_line((-0.7854, 0, 0), 'Diagonal Line 2')


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
