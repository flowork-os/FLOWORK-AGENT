# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_sandwich_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate sandwich using Blender code

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich
materials_list = [
    ('Bread', (0.9, 0.7, 0.5, 1)),
    ('Lettuce', (0.2, 0.8, 0.2, 1)),
    ('Tomato', (0.8, 0.1, 0.1, 1)),
    ('Cheese', (1, 0.9, 0.1, 1)),
    ('Ham', (0.9, 0.5, 0.5, 1))
]

# Function to create a material

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

materials = {name: create_material(name, color) for name, color in materials_list}

# Function to create a sandwich layer

def create_layer(size, location, name, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    layer = bpy.context.object
    layer.name = name
    layer.scale[2] = scale
    layer.data.materials.append(material)

# Create sandwich layers
create_layer(2, (0, 0, 0.25), 'Bread Slice 1', 0.1, materials['Bread'])
create_layer(2, (0, 0, -0.25), 'Bread Slice 2', 0.1, materials['Bread'])
create_layer(2, (0, 0, 0.15), 'Lettuce', 0.05, materials['Lettuce'])
create_layer(2, (0, 0, 0.05), 'Tomato', 0.05, materials['Tomato'])
create_layer(2, (0, 0, -0.05), 'Cheese', 0.05, materials['Cheese'])
create_layer(2, (0, 0, -0.15), 'Ham', 0.05, materials['Ham'])

# Create Toothpick
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1, location=(0, 0, 0.5))
toothpick = bpy.context.object

toothpick.name = 'Toothpick'
toothpick.data.materials.append(materials['Bread'])

# Create Flag
bpy.ops.mesh.primitive_plane_add(size=0.3, location=(0, 0.15, 0.85))
flag = bpy.context.object
flag.name = 'Flag'
flag.rotation_euler[1] = 1.5708
flag.data.materials.append(materials['Tomato'])

# Create Plate
bpy.ops.mesh.primitive_cylinder_add(radius=3, depth=0.1, location=(0, 0, -0.35))
plate = bpy.context.object
plate.name = 'Plate'
plate.data.materials.append(materials['Bread'])


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
