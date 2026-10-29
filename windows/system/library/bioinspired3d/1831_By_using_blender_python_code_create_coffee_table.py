# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_python_code_create_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender python code create coffee table.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the table
wood_material = bpy.data.materials.new(name='Wooden Finish')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Rich brown color

# Function to create a cube with specific dimensions and location
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Generate the table top
create_cube(2, (0, 0, 0.75), 'Table Surface', wood_material)

table_surface = bpy.context.object
table_surface.scale[0] = 1.5
table_surface.scale[1] = 0.75
table_surface.scale[2] = 0.1

# Create table legs using a loop
leg_height = 0.75
leg_radius = 0.05
leg_positions = [(-1.4, -0.7, leg_height / 2), (1.4, -0.7, leg_height / 2), (-1.4, 0.7, leg_height / 2), (1.4, 0.7, leg_height / 2)]

for index, position in enumerate(leg_positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=position)
    leg = bpy.context.object
    leg.name = f'Leg {index + 1}'
    leg.data.materials.append(wood_material)

# Create the lower shelf using the helper function
create_cube(2, (0, 0, 0.25), 'Shelf', wood_material)

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
