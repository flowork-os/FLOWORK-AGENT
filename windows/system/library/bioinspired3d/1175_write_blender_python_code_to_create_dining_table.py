# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_python_code_to_create_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender python code to create dining table

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table
material_wood = bpy.data.materials.new(name='Wooden Finish')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a table top

def create_table_top():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    top = bpy.context.object
    top.scale[0] = 2.5  # Length
    top.scale[1] = 1.2  # Width
    top.scale[2] = 0.1  # Thickness
    top.name = 'Table Surface'
    top.data.materials.append(material_wood)

# Function to create table legs

def create_table_legs():
    positions = [(-2.4, -1.1, 0.5), (2.4, -1.1, 0.5), (-2.4, 1.1, 0.5), (2.4, 1.1, 0.5)]
    for index, position in enumerate(positions):
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=position)
        leg = bpy.context.object
        leg.scale[2] = 5  # Height
        leg.name = f'Leg {index + 1}'
        leg.data.materials.append(material_wood)

# Create the table
create_table_top()
create_table_legs()


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
