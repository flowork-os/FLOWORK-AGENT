# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_sandwich_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make sandwich using code in Blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
light_brown = bpy.data.materials.new(name='Light Brown Bread')
light_brown.diffuse_color = (0.9, 0.7, 0.5, 1)
green_lettuce = bpy.data.materials.new(name='Green Lettuce')
green_lettuce.diffuse_color = (0.2, 0.8, 0.2, 1)
red_tomato = bpy.data.materials.new(name='Red Tomato')
red_tomato.diffuse_color = (0.8, 0.1, 0.1, 1)
yellow_cheese = bpy.data.materials.new(name='Yellow Cheese')
yellow_cheese.diffuse_color = (1, 0.9, 0.1, 1)
pink_ham = bpy.data.materials.new(name='Pink Ham')
pink_ham.diffuse_color = (0.9, 0.5, 0.5, 1)

# Function to create a cube with material

def create_cube(size, location, name, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = scale
    cube.data.materials.append(material)

# Create Bread Slices
create_cube(2, (0, 0, 0.25), 'Bread Slice 1', 0.1, light_brown)
create_cube(2, (0, 0, -0.25), 'Bread Slice 2', 0.1, light_brown)

# Create Lettuce Layer
create_cube(2, (0, 0, 0.15), 'Lettuce', 0.05, green_lettuce)

# Create Tomato Layer
create_cube(2, (0, 0, 0.05), 'Tomato', 0.05, red_tomato)

# Create Cheese Layer
create_cube(2, (0, 0, -0.05), 'Cheese', 0.05, yellow_cheese)

# Create Ham Layer
create_cube(2, (0, 0, -0.15), 'Ham', 0.05, pink_ham)

# Create Toothpick
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1, location=(0, 0, 0.5))
toothpick = bpy.context.object

toothpick.name = 'Toothpick'
toothpick.data.materials.append(light_brown)

# Create Flag
bpy.ops.mesh.primitive_plane_add(size=0.3, location=(0, 0.15, 0.85))
flag = bpy.context.object
flag.name = 'Flag'
flag.rotation_euler[1] = 1.5708
flag.data.materials.append(red_tomato)

# Create Plate
bpy.ops.mesh.primitive_cylinder_add(radius=3, depth=0.1, location=(0, 0, -0.35))
plate = bpy.context.object
plate.name = 'Plate'
plate.data.materials.append(light_brown)


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
