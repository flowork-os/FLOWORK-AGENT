# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_coffee_table_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of coffee table using code in Blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_texture = bpy.data.materials.new(name='Wood Texture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Add the table top as a scaled cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
table = bpy.context.object

table.scale = (2, 1, 0.1)
table.name = 'Wooden Table Top'
table.data.materials.append(wood_texture)

# Create table legs at specified locations
legs_info = [(-1.9, -0.9, 0.25), (1.9, -0.9, 0.25), (-1.9, 0.9, 0.25), (1.9, 0.9, 0.25)]
leg_height = 0.5
leg_radius = 0.05

for index, coordinates in enumerate(legs_info):
    bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=coordinates)
    leg_object = bpy.context.object
    leg_object.name = f'Table Leg {index + 1}'
    leg_object.data.materials.append(wood_texture)


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
