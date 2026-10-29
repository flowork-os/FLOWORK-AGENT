# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_build_toy_rocket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to build toy rocket.

import bpy
import math

# Clear the current mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for different components
material_red = bpy.data.materials.new(name='Red')
material_red.diffuse_color = (0.8, 0.1, 0.1, 1)
material_blue = bpy.data.materials.new(name='Blue')
material_blue.diffuse_color = (0.1, 0.1, 0.8, 1)
material_gray = bpy.data.materials.new(name='Gray')
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the body of the rocket
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=3, location=(0, 0, 1.5))
rocket_body = bpy.context.object
rocket_body.name = 'Rocket Body'
rocket_body.data.materials.append(material_red)

# Add the top cone
bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1, location=(0, 0, 3.5))
nose_tip = bpy.context.object
nose_tip.name = 'Nose Tip'
nose_tip.data.materials.append(material_red)

# Function to create fins

def create_fins():
    for j in range(3):
        theta = j * (2 * math.pi / 3)
        fin_x_pos = 0.5 * math.cos(theta)
        fin_y_pos = 0.5 * math.sin(theta)
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(fin_x_pos, fin_y_pos, 0.25))
        fin_part = bpy.context.object
        fin_part.name = f'Fin {j + 1}'
        fin_part.scale[1] = 0.1
        fin_part.scale[2] = 2
        fin_part.rotation_euler[2] = theta
        fin_part.data.materials.append(material_blue)

# Create the fins
create_fins()

# Create the window
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0.5, 0, 2.5))
view_window = bpy.context.object
view_window.name = 'Rocket Window'
view_window.data.materials.append(material_gray)


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
