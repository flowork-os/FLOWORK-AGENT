# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_router_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build router in python blender code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
mat_black = bpy.data.materials.new(name='Black_Material')
mat_black.diffuse_color = (0, 0, 0, 1)
mat_green = bpy.data.materials.new(name='Green_Material')
mat_green.diffuse_color = (0, 1, 0, 1)
mat_blue = bpy.data.materials.new(name='Blue_Material')
mat_blue.diffuse_color = (0, 0, 1, 1)

# Create a base object
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_object = bpy.context.object
base_object.name = 'Base_Object'
base_object.scale = (1, 0.5, 0.1)
base_object.data.materials.append(mat_black)

# Generate antennas
for index in range(4):
    x_coord = 0.9 * (index % 2) - 0.45
    y_coord = 0.45 * (index // 2) - 0.225
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_coord, y_coord, 1.1))
    antenna_object = bpy.context.object
    antenna_object.name = 'Antenna_' + str(index + 1)
    antenna_object.data.materials.append(mat_black)

# Create indicator lights
for index in range(3):
    x_coord = 0.6 - index * 0.4
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_coord, 0.55, 0.6))
    light_object = bpy.context.object
    light_object.name = 'Indicator_Light_' + str(index + 1)
    light_object.data.materials.append(mat_green)

# Create ports
for index in range(3):
    x_coord = -0.6 + index * 0.4
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(x_coord, -0.55, 0.6))
    port_object = bpy.context.object
    port_object.name = 'Port_' + str(index + 1)
    port_object.data.materials.append(mat_black)


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
