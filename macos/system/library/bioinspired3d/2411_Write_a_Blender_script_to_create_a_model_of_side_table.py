# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_script_to_create_a_model_of_side_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender script to create a model of side table

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the table
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a cube for the table top
def create_table_top():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    top = bpy.context.object
    top.name = 'TableTop'
    top.scale = (1.0, 1.0, 0.1)
    top.data.materials.append(wood_material)

create_table_top()

# Function to create table legs
def create_leg(index):
    x_position = 0.45 * (index % 2) - 0.225
    y_position = 0.45 * (index // 2) - 0.225
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(x_position, y_position, 0.25))
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(wood_material)

# Create all four legs
for i in range(4):
    create_leg(i)


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
