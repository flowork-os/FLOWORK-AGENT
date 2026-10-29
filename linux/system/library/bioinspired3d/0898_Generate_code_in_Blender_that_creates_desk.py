# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_code_in_Blender_that_creates_desk" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate code in Blender that creates desk.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_material = bpy.data.materials.new(name='Wood Grain')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a cube

def create_cube(size, location, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    return cube

# Create the desk top
desk_surface = create_cube(2, (0, 0, 0.5), 'Desk Surface')
desk_surface.scale[0] = 2

desk_surface.scale[1] = 1

desk_surface.scale[2] = 0.1

desk_surface.data.materials.append(wood_material)

# Function to create legs

def create_leg(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=location)
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    return leg

# Define leg positions
leg_positions = [(-1.9, -0.9, 0.25), (1.9, -0.9, 0.25), (-1.9, 0.9, 0.25), (1.9, 0.9, 0.25)]

# Create legs
for index, position in enumerate(leg_positions):
    create_leg(position).name = f'Leg_{index + 1}'


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
