# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_dining_table_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make dining table using python blender code

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the table
wood_material = bpy.data.materials.new(name="Wood")
wood_material.diffuse_color = (0.64, 0.32, 0.18, 1)  # A rich brown color

# Function to create the table top

def create_table_top(size, location):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    top = bpy.context.object
    top.scale = (1.5, 1, 0.1)  # Set dimensions
    top.name = "Table Surface"
    top.data.materials.append(wood_material)
    return top

# Create the table top
create_table_top(2, (0, 0, 1))

# Function to create a leg

def create_leg(radius, height, position):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    return leg

# Define leg parameters
leg_height = 0.9
leg_radius = 0.05
leg_coords = [(-1.4, -0.9, leg_height / 2), (1.4, -0.9, leg_height / 2), (-1.4, 0.9, leg_height / 2), (1.4, 0.9, leg_height / 2)]

# Create the legs
for index, coord in enumerate(leg_coords):
    create_leg(leg_radius, leg_height, coord)


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
