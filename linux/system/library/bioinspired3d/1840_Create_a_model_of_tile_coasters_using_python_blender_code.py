# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_tile_coasters_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of tile coasters using python blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the coasters
coaster_material = bpy.data.materials.new(name='CoasterMaterial')
coaster_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray

# Function to create a coaster at a specified position
def create_coaster(index, x_pos, y_pos):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.5, depth=0.1, location=(x_pos, y_pos, 0))
    coaster_obj = bpy.context.object
    coaster_obj.name = f'Coaster_{index + 1}'
    coaster_obj.data.materials.append(coaster_material)

# Generate coasters in a grid
for idx in range(4):
    x_coord = 4 * (idx % 2) - 2
    y_coord = 4 * (idx // 2) - 2
    create_coaster(idx, x_coord, y_coord)


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
