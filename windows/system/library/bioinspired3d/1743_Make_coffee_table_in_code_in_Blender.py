# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_coffee_table_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make coffee table in code in Blender

import bpy

# Reset the scene to start fresh
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table
material_table = bpy.data.materials.new(name='Table Wood')
material_table.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the table top using a primitive cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
table_surface = bpy.context.object

table_surface.scale[0] = 2  # Length
table_surface.scale[1] = 1  # Width
table_surface.scale[2] = 0.1  # Thickness

table_surface.name = 'Table Surface'
table_surface.data.materials.append(material_table)

# Create legs using a loop
legs = []
leg_height = 0.5
leg_radius = 0.05
leg_coordinates = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]

for idx, coord in enumerate(leg_coordinates):
    bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=coord)
    leg = bpy.context.object
    leg.name = f'Leg {idx + 1}'
    leg.data.materials.append(material_table)
    legs.append(leg)


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
