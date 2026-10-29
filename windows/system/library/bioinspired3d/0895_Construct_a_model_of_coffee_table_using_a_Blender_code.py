# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_coffee_table_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of coffee table using a Blender code

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Function to create a table leg

def create_leg(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=location)
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    leg.name = 'Table Leg'

# Create the tabletop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
tabletop = bpy.context.object

tabletop.scale[0] = 2  # Length

tabletop.scale[1] = 1  # Width

tabletop.scale[2] = 0.1  # Thickness

tabletop.name = 'Tabletop'
tabletop.data.materials.append(wood_material)

# Positions for the legs
leg_positions = [(-1.9, -0.9, 0.25), (1.9, -0.9, 0.25), (-1.9, 0.9, 0.25), (1.9, 0.9, 0.25)]

# Create all four legs
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
