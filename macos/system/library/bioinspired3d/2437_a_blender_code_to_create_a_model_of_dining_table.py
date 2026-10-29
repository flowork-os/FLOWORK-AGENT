# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_create_a_model_of_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to create a model of dining table.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new wood material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a table leg
def create_leg(x_pos, y_pos, height, radius):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(x_pos, y_pos, height / 2))
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    return leg

# Create the table top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
table_surface = bpy.context.object
# Scale the table top
scale_factors = (1.5, 1, 0.1)
table_surface.scale = scale_factors

table_surface.name = 'Table Surface'
table_surface.data.materials.append(wood_material)

# Dimensions for legs
leg_height = 1
leg_radius = 0.1

# Create four legs using the helper function
for index in range(4):
    leg_x = 1.4 * (index % 2) - 0.7
    leg_y = 0.9 * (index // 2) - 0.45
    create_leg(leg_x, leg_y, leg_height, leg_radius)


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
