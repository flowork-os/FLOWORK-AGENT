# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates a model of coffee table.

import bpy

# Clear the existing scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table surface
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown color for wood

# Function to build the table

def build_table():
    # Create the main tabletop
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    tabletop = bpy.context.object
    tabletop.name = 'Main Tabletop'
    tabletop.scale.x = 2  # Length
    tabletop.scale.y = 1  # Width
    tabletop.scale.z = 0.1  # Thickness
    tabletop.data.materials.append(wood_material)

    # Create table legs
    leg_height = 0.5
    leg_radius = 0.05
    leg_positions = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]

    for index, position in enumerate(leg_positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=position)
        leg = bpy.context.object
        leg.name = f'Leg_{index + 1}'
        leg.data.materials.append(wood_material)

build_table()


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
