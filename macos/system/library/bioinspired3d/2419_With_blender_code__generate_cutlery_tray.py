# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code__generate_cutlery_tray" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code, generate cutlery tray

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the tray
tray_material = bpy.data.materials.new(name='TrayMaterial')
tray_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray color

# Function to create a cube with specified parameters
def create_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(tray_material)
    return cube

# Create the tray base
base_cube = create_cube(2, (0, 0, 0), 'TrayBase', (1, 1, 0.1))

# Divider specifications
divider_thin = 0.05
divider_tall = 0.2

# Create horizontal dividers
for index in range(1, 3):
    create_cube(1, (0, index * 0.5 - 0.5, 0.1), f'HorizontalDivider_{index}', (1, divider_thin, divider_tall))

# Create vertical dividers
for index in range(1, 4):
    create_cube(1, (index * 0.5 - 1, 0, 0.1), f'VerticalDivider_{index}', (divider_thin, 1, divider_tall))


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
