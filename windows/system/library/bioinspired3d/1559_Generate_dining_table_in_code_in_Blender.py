# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_dining_table_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate dining table in code in Blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the wood texture
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the table top using a function
def add_table_top():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
    top = bpy.context.object
    top.scale[0] = 2  # Length
    top.scale[1] = 1  # Width
    top.scale[2] = 0.1  # Thickness
    top.name = 'Table Top'
    top.data.materials.append(wood_texture)
    return top

# Function to create legs
def add_leg(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.75, location=(x, y, z))
    leg = bpy.context.object
    leg.data.materials.append(wood_texture)
    leg.name = 'Table Leg'

# Create the table top
add_table_top()

# Create each leg
add_leg(-1.8, -0.9, 0.375)
add_leg(1.8, -0.9, 0.375)
add_leg(-1.8, 0.9, 0.375)
add_leg(1.8, 0.9, 0.375)


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
