# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_to_make_centrifuge" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code to make centrifuge.

import bpy
import math

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a material with a specified color

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create materials
body_mat = create_material('Body Material', (0.5, 0.5, 0.5, 1))
lid_mat = create_material('Lid Material', (0.7, 0.7, 0.7, 1))
panel_mat = create_material('Panel Material', (0.2, 0.2, 0.2, 1))
button_mat = create_material('Button Material', (0, 0, 1, 1))
screen_mat = create_material('Screen Material', (0, 1, 0, 1))

# Function to add a cylinder

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Function to add a cube

def add_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the centrifuge components
body = add_cylinder(1, 1.5, (0, 0, 0.75), 'Centrifuge Body', body_mat)
lid = add_cylinder(1.05, 0.2, (0, 0, 1.5), 'Centrifuge Lid', lid_mat)
panel = add_cube(0.5, (0, 1.1, 0.75), 'Control Panel', panel_mat)
panel.scale[2] = 0.1

# Create buttons
for i in range(3):
    add_cube(0.1, (-0.15 + i * 0.15, 1.15, 0.75), f'Button {i + 1}', button_mat)

# Create display screen
add_cube(0.2, (0.3, 1.15, 0.75), 'Display Screen', screen_mat)

# Create test tube slots
for i in range(6):
    angle = math.radians(i * 60)
    x = 0.5 * math.cos(angle)
    y = 0.5 * math.sin(angle)
    add_cylinder(0.1, 0.5, (x, y, 0.25), f'Test Tube Slot {i + 1}', body_mat)


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
