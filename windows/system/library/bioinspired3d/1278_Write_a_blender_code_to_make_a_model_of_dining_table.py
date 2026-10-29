# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_to_make_a_model_of_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code to make a model of dining table

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table
material_wood = bpy.data.materials.new(name="Wood")
material_wood.diffuse_color = (0.64, 0.32, 0.18, 1)

# Add the table top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
table_surface = bpy.context.object

table_surface.scale[0] = 1.5  # Length

table_surface.scale[1] = 1  # Width

table_surface.scale[2] = 0.1  # Thickness

table_surface.name = "Table Surface"
table_surface.data.materials.append(material_wood)

# Define leg attributes
height_of_leg = 0.9
radius_of_leg = 0.05
positions_of_legs = [(-1.4, -0.9, 0), (1.4, -0.9, 0), (-1.4, 0.9, 0), (1.4, 0.9, 0)]

# Create the legs using a loop
for index, position in enumerate(positions_of_legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_leg, depth=height_of_leg, location=(position[0], position[1], height_of_leg / 2))
    leg = bpy.context.object
    leg.name = f"Leg_{index + 1}"
    leg.data.materials.append(material_wood)


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
