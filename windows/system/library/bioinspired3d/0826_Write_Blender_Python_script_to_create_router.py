# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_to_create_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script to create router.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
black_material = bpy.data.materials.new(name='Black_Material')
black_material.diffuse_color = (0, 0, 0, 1)
green_material = bpy.data.materials.new(name='Green_Material')
green_material.diffuse_color = (0, 1, 0, 1)

# Create the base shape
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_shape = bpy.context.object
base_shape.name = 'Base_Shape'
base_shape.scale = (1, 0.5, 0.1)
base_shape.data.materials.append(black_material)

# Function to add antennas
def add_antennas():
    for i in range(4):
        x_pos = 0.9 * (i % 2) - 0.45
        y_pos = 0.45 * (i // 2) - 0.225
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_pos, y_pos, 1.1))
        antenna_obj = bpy.context.object
        antenna_obj.name = f'Antenna_{i + 1}'
        antenna_obj.data.materials.append(black_material)

# Function to add indicator lights
def add_indicator_lights():
    for i in range(3):
        x_pos = 0.6 - i * 0.4
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_pos, 0.55, 0.6))
        light_obj = bpy.context.object
        light_obj.name = f'Indicator_Light_{i + 1}'
        light_obj.data.materials.append(green_material)

# Function to create ports
def create_ports():
    for i in range(3):
        x_pos = -0.6 + i * 0.4
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=(x_pos, -0.55, 0.6))
        port_obj = bpy.context.object
        port_obj.name = f'Port_{i + 1}'
        port_obj.data.materials.append(black_material)

# Call functions to create the model
add_antennas()
add_indicator_lights()
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
