# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_dining_table_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create dining table in blender python code

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table
material_wood = bpy.data.materials.new(name='WoodMaterial')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function for creating the table
def build_table():
    # Create the tabletop
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
    tabletop = bpy.context.object
    tabletop.scale = (2, 1, 0.1)
    tabletop.name = 'Tabletop'
    tabletop.data.materials.append(material_wood)

    # Create legs
    leg_positions = [(-1.8, -0.9, 0.375), (1.8, -0.9, 0.375), (-1.8, 0.9, 0.375), (1.8, 0.9, 0.375)]
    for i, pos in enumerate(leg_positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.75, location=pos)
        leg = bpy.context.object
        leg.name = f'Leg_{i + 1}'
        leg.data.materials.append(material_wood)

# Execute table building function
build_table()


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
