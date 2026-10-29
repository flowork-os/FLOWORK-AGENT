# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_make_a_model_of_centrifuge" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to make a model of centrifuge

import bpy
import math

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
mat_gray = bpy.data.materials.new(name="Gray Material")
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
mat_dark = bpy.data.materials.new(name="Dark Material")
mat_dark.diffuse_color = (0.2, 0.2, 0.2, 1)
mat_blue = bpy.data.materials.new(name="Blue Material")
mat_blue.diffuse_color = (0.0, 0.0, 1.0, 1)

# Create the main body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
body = bpy.context.object
body.name = "Centrifuge Base"
body.data.materials.append(mat_gray)

# Create the rotor
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 2))
rotor = bpy.context.object
rotor.name = "Centrifuge Rotor"
rotor.data.materials.append(mat_dark)

# Create sample holders using a loop
for i in range(4):
    theta = i * (math.pi / 2)
    pos_x = 0.7 * math.cos(theta)
    pos_y = 0.7 * math.sin(theta)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(pos_x, pos_y, 2.1), rotation=(math.pi / 2, 0, theta))
    holder = bpy.context.object
    holder.name = f"Sample Holder {i + 1}"
    holder.data.materials.append(mat_dark)

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1.1, 0, 1.5))
control_panel = bpy.context.object
control_panel.name = "Centrifuge Control Panel"
control_panel.data.materials.append(mat_blue)


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
