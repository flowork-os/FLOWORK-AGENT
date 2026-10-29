# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code_build_a_model_of_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code build a model of router.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
material_body = bpy.data.materials.new(name='Router Surface')
material_body.diffuse_color = (0.1, 0.1, 0.1, 1)
material_led = bpy.data.materials.new(name='Indicator Light')
material_led.diffuse_color = (0, 1, 0, 1)
material_port = bpy.data.materials.new(name='Connection Port')
material_port.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a cube
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the router body
body = create_cube(2, (0, 0, 0.5), 'Router Base', material_body)
body.scale = (2, 1, 0.2)

# Create antennas
for index in range(3):
    pos_x = (index - 1) * 1.5
    create_cylinder(0.05, 1, (pos_x, 0, 1.2), f'Antenna_{index + 1}', material_body)

# Create LED indicators
for index in range(5):
    pos_x = (index - 2) * 0.5
    create_cube(0.1, (pos_x, 1.1, 0.6), f'LED_{index + 1}', material_led)

# Create ports
for index in range(4):
    pos_x = (index - 1.5) * 0.5
    create_cube(0.2, (pos_x, -1.1, 0.6), f'Port_{index + 1}', material_port)


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
