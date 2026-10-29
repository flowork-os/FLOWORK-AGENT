# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_makes_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that makes a model of coffee table.

import bpy

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_texture = bpy.data.materials.new(name='Wood Texture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Classic wood color

# Function to add a scaled cube
def add_scaled_cube(size, position, name, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(mat)
    return cube

# Create the tabletop
add_scaled_cube(2, (0, 0, 0.75), 'Top', wood_texture)

table_top = bpy.context.object
table_top.scale[0] = 1.5
table_top.scale[1] = 0.75
table_top.scale[2] = 0.1

# Define leg specifications
height_of_legs = 0.75
radius_of_legs = 0.05
leg_coordinates = [(-1.4, -0.7, height_of_legs / 2), (1.4, -0.7, height_of_legs / 2), (-1.4, 0.7, height_of_legs / 2), (1.4, 0.7, height_of_legs / 2)]

for index, coord in enumerate(leg_coordinates):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_legs, depth=height_of_legs, location=coord)
    leg = bpy.context.object
    leg.name = f'Leg {index + 1}'
    leg.data.materials.append(wood_texture)

# Create the lower shelf
add_scaled_cube(2, (0, 0, 0.25), 'Shelf', wood_texture)

shelf = bpy.context.object
shelf.scale[0] = 1.4
shelf.scale[1] = 0.7
shelf.scale[2] = 0.05


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
