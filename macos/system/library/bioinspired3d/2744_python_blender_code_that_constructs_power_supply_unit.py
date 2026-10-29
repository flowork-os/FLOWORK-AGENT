# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_constructs_power_supply_unit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that constructs power supply unit.

import bpy

# Function to clear the scene
def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Clear the scene
clear_scene()

# Create materials
material_gray = bpy.data.materials.new(name='GrayMaterial')
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

material_dark = bpy.data.materials.new(name='DarkMaterial')
material_dark.diffuse_color = (0, 0, 0, 1)

# Create the PSU body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
body = bpy.context.object
body.name = 'PowerSupplyBody'
body.scale = (1.5, 1, 0.5)
body.data.materials.append(material_gray)

# Create fan with a cylinder
fan_location = (1.5, 0, 0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.1, location=fan_location)
fan = bpy.context.object
fan.name = 'FanUnit'
fan.rotation_euler = (0, 1.5708, 0)
fan.data.materials.append(material_dark)

# Create power switch
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(-1.5, 0.4, 0.2))
switch = bpy.context.object
switch.name = 'SwitchUnit'
switch.data.materials.append(material_dark)

# Create power port
bpy.ops.mesh.primitive_cube_add(size=0.3, location=(-1.5, -0.4, 0.2))
port = bpy.context.object
port.name = 'PortUnit'
port.data.materials.append(material_dark)

# Create ventilation holes
for x in range(-5, 6):
    for y in range(-2, 3):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.1, location=(x * 0.3, y * 0.3, 0.5))
        vent_top = bpy.context.object
        vent_top.name = f'VentHoleTop_{x}_{y}'
        vent_top.rotation_euler = (1.5708, 0, 0)
        vent_top.data.materials.append(material_dark)

for x in range(-3, 4):
    for y in range(-1, 2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.1, location=(1.5, x * 0.3, y * 0.3))
        vent_side = bpy.context.object
        vent_side.name = f'VentHoleSide_{x}_{y}'
        vent_side.rotation_euler = (0, 1.5708, 0)
        vent_side.data.materials.append(material_dark)

# Create label plane
bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, -1.01, 0))
label_plane = bpy.context.object
label_plane.name = 'LabelPlane'
label_plane.rotation_euler = (1.5708, 0, 0)
label_plane.data.materials.append(material_gray)

# Create label text
bpy.ops.object.text_add(location=(0, -1.01, 0.1))
label_text = bpy.context.object
label_text.name = 'LabelText'
label_text.data.body = 'Voltage: 230V\nWattage: 500W'
label_text.rotation_euler = (1.5708, 0, 0)
label_text.scale = (0.1, 0.1, 0.1)
label_text.data.materials.append(material_dark)


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
