# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code__create_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code, create a model of coffee table.

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the table
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Function to create a cube

def create_tabletop():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.4))
    tabletop = bpy.context.object
    tabletop.scale = (0.5, 1, 0.05)  # Making it flat
    tabletop.name = 'Tabletop'
    tabletop.data.materials.append(wood_material)

# Function to create legs

def create_leg(location, index):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.4, location=location)
    leg = bpy.context.object
    leg.name = f'Leg_{index}'
    leg.data.materials.append(wood_material)

# Create the tabletop
create_tabletop()

# Leg positions
positions = [(-0.45, -0.95, 0.2), (0.45, -0.95, 0.2), (-0.45, 0.95, 0.2), (0.45, 0.95, 0.2)]

# Create each leg using a loop
for idx, pos in enumerate(positions):
    create_leg(pos, idx + 1)


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
