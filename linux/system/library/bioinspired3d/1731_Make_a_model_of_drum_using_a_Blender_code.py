# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_drum_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of drum using a Blender code

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts of the drum
body_color = bpy.data.materials.new(name='Body Color')
body_color.diffuse_color = (0.5, 0.25, 0.1, 1)
drumhead_color = bpy.data.materials.new(name='Drumhead Color')
drumhead_color.diffuse_color = (0.8, 0.8, 0.8, 1)
tension_color = bpy.data.materials.new(name='Tension Color')
tension_color.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to add a cylinder
def add_cylinder(radius, height, position, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)

# Adding drum body
add_cylinder(1, 1.5, (0, 0, 0.75), 'Drum Body', body_color)

# Adding drumhead
add_cylinder(1.05, 0.1, (0, 0, 1.55), 'Drumhead', drumhead_color)

# Adding tension rods
for i in range(8):
    angle = i * (2 * math.pi / 8)
    rod_x = 1.1 * math.cos(angle)
    rod_y = 1.1 * math.sin(angle)
    add_cylinder(0.05, 1.6, (rod_x, rod_y, 0.8), f'Tension Rod {i + 1}', tension_color)


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
