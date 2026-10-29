# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_create_mandala_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to create mandala design.

import bpy
import math

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with distinct colors
red_material = bpy.data.materials.new(name='RedMaterial')
red_material.diffuse_color = (0.8, 0.1, 0.1, 1)
green_material = bpy.data.materials.new(name='GreenMaterial')
green_material.diffuse_color = (0.1, 0.8, 0.1, 1)
blue_material = bpy.data.materials.new(name='BlueMaterial')
blue_material.diffuse_color = (0.1, 0.1, 0.8, 1)

# Function to create a circle with a given radius and material

def create_circle(radius, location, name, material):
    bpy.ops.mesh.primitive_circle_add(radius=radius, location=location)
    circle = bpy.context.object
    circle.name = name
    circle.data.materials.append(material)
    return circle

# Create the central circle
central = create_circle(1, (0, 0, 0), 'Central Circle', red_material)

# Create concentric rings
for index in range(1, 4):
    create_circle(1 + index, (0, 0, 0), f'Ring {index}', green_material if index % 2 == 0 else blue_material)

# Function to create petals

def create_petal(index, angle):
    x = (1.5 + 0.5) * math.cos(angle)
    y = (1.5 + 0.5) * math.sin(angle)
    create_circle(0.5, (x, y, 0), f'Petal {index + 1}', red_material)

# Create petals
petals_count = 12
for i in range(petals_count):
    petal_angle = i * (2 * math.pi / petals_count)
    create_petal(i, petal_angle)

# Function to create lines

def create_line(index, angle):
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3, location=(x / 2, y / 2, 0), rotation=(0, 0, angle))
    line = bpy.context.object
    line.name = f'Line {index + 1}'
    line.data.materials.append(blue_material)

# Create radiating lines
lines_count = 24
for i in range(lines_count):
    line_angle = i * (2 * math.pi / lines_count)
    create_line(i, line_angle)


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
