# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_building_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for building router

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_black = bpy.data.materials.new(name='Material_Black')
material_black.diffuse_color = (0, 0, 0, 1)
material_green = bpy.data.materials.new(name='Material_Green')
material_green.diffuse_color = (0, 1, 0, 1)
material_blue = bpy.data.materials.new(name='Material_Blue')
material_blue.diffuse_color = (0, 0, 1, 1)

# Function to create a base
def create_base():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    base_object = bpy.context.object
    base_object.name = 'Base'
    base_object.scale = (1, 0.5, 0.1)
    base_object.data.materials.append(material_black)

# Function to create antennas
def create_antennas():
    for index in range(4):
        x_position = 0.9 * (index % 2) - 0.45
        y_position = 0.45 * (index // 2) - 0.225
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_position, y_position, 1.1))
        antenna_object = bpy.context.object
        antenna_object.name = f'Antenna_{index + 1}'
        antenna_object.data.materials.append(material_black)

# Function to create indicator lights
def create_indicator_lights():
    for index in range(3):
        x_position = 0.6 - index * 0.4
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_position, 0.55, 0.6))
        light_object = bpy.context.object
        light_object.name = f'Light_{index + 1}'
        light_object.data.materials.append(material_green)

# Function to create ports
def create_ports():
    for index in range(3):
        x_position = -0.6 + index * 0.4
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=(x_position, -0.55, 0.6))
        port_object = bpy.context.object
        port_object.name = f'Port_{index + 1}'
        port_object.data.materials.append(material_black)

# Execute creation functions
create_base()
create_antennas()
create_indicator_lights()
create_ports()


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
