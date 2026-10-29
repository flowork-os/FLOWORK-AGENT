# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_coffee_table_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of coffee table in code in Blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the wood material
wood_texture = bpy.data.materials.new(name='Wood Texture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the tabletop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
table_surface = bpy.context.object

table_surface.scale[0] = 2  # Length

table_surface.scale[1] = 1  # Width

table_surface.scale[2] = 0.1  # Thickness

table_surface.name = 'Table Surface'
table_surface.data.materials.append(wood_texture)

# Create table legs at specified positions
leg_positions = [(-1.9, -0.9, 0.375), (1.9, -0.9, 0.375), (-1.9, 0.9, 0.375), (1.9, 0.9, 0.375)]

for index, position in enumerate(leg_positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.75, location=position)
    leg = bpy.context.object
    leg.name = f'Leg {index + 1}'
    leg.data.materials.append(wood_texture)


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
