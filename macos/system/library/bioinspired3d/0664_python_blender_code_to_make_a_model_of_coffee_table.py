# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a model of coffee table.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood-like material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # RGB for brown wood

# Function to create a table top

def create_table_top():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    top = bpy.context.object
    top.name = 'Table Surface'
    top.scale[0] = 2  # Length
    top.scale[1] = 1  # Width
    top.scale[2] = 0.1  # Thickness
    top.data.materials.append(wood_material)

create_table_top()

# Function to create table legs

def create_legs():
    height = 0.5
    radius = 0.05
    positions = [(-1.9, -0.9, height / 2), (1.9, -0.9, height / 2), (-1.9, 0.9, height / 2), (1.9, 0.9, height / 2)]

    for index, position in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        leg = bpy.context.object
        leg.name = f'Leg {index + 1}'
        leg.data.materials.append(wood_material)

create_legs()


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
