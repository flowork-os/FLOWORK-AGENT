# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_coffee_table_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of coffee table in blender python code

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new wood material
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a table leg
def create_leg(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.75, location=location)
    leg = bpy.context.object
    leg.data.materials.append(wood_material)
    return leg

# Create the table top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
table_top = bpy.context.object

table_top.scale[0] = 2  # Length
table_top.scale[1] = 1  # Width
table_top.scale[2] = 0.1  # Thickness

table_top.name = 'Table Top'
table_top.data.materials.append(wood_material)

# Define leg positions
leg_positions = [(-1.9, -0.9, 0.375), (1.9, -0.9, 0.375), (-1.9, 0.9, 0.375), (1.9, 0.9, 0.375)]

# Create table legs using the defined positions
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
