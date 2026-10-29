# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code_build_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code build coffee table.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Rich brown color

# Function to create a table leg
def create_leg(position, height, radius):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    return leg

# Create the table top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
table_surface = bpy.context.object

# Scale the table top dimensions
scale_factors = (2, 1, 0.1)
table_surface.scale = scale_factors

# Assign the material to the table top
bpy.context.object.data.materials.append(wood_material)

# Define the dimensions for the legs
leg_height = 0.5
leg_radius = 0.05
leg_positions = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]

# Create legs using the helper function
for position in leg_positions:
    create_leg(position, leg_height, leg_radius)


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
