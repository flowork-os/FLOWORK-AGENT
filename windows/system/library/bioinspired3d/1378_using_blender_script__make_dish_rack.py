# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script__make_dish_rack" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script, make dish rack.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a metallic material
metal_material = bpy.data.materials.new(name='Metal Surface')
metal_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light gray color

# Function to create and configure a cube
def setup_cube(size, loc, name, scale_factors):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale_factors
    cube.data.materials.append(metal_material)

# Create the flat base
setup_cube(2, (0, 0, 0.1), 'Flat Base', (1, 1, 0.025))

# Create side bars
for i in range(2):
    x_coord = 0.9 * (i * 2 - 1)
    setup_cube(2, (x_coord, 0, 0.6), f'Side Bar {i + 1}', (0.05, 1, 0.5))

# Create horizontal racks
for i in range(5):
    y_coord = 0.8 * (i / 4) - 0.4
    setup_cube(2, (0, y_coord, 0.6), f'Rack {i + 1}', (0.9, 0.05, 0.05))


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
