# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_code_in_Blender_that_makes_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate code in Blender that makes coffee table

import bpy

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the table
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Set the wood color

# Function to create a cube with specified dimensions
def create_cube(size, location, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = (size * 1, size * 0.5, 0.05)
    cube.name = name
    cube.data.materials.append(wood_material)
    return cube

# Create the table top
create_cube(2, (0, 0, 0.5), 'Table Top')

# Function to create a leg at a specific position
def create_leg(position):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=position)
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    return leg

# Define the positions for the legs
leg_positions = [(-1.9, -0.9, 0.25), (1.9, -0.9, 0.25), (-1.9, 0.9, 0.25), (1.9, 0.9, 0.25)]

# Create legs using the defined positions
for position in leg_positions:
    create_leg(position)


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
