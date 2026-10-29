# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_coffee_table_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of coffee table in a Blender script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define wood material
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Representing wood

# Function to generate the tabletop
def generate_tabletop():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.4))
    tabletop = bpy.context.object
    tabletop.scale = (0.5, 1, 0.05)
    tabletop.name = 'Tabletop'
    tabletop.data.materials.append(wood_texture)

# Function to create table legs at specified locations
def generate_legs():
    leg_coords = [(-0.45, -0.95, 0.2), (0.45, -0.95, 0.2), (-0.45, 0.95, 0.2), (0.45, 0.95, 0.2)]
    for index, coord in enumerate(leg_coords):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.4, location=coord)
        leg = bpy.context.object
        leg.name = f'Leg_{index + 1}'
        leg.data.materials.append(wood_texture)

# Create the tabletop and legs
generate_tabletop()
generate_legs()


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
