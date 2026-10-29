# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code_construct_dish_rack" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code construct dish rack

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a gray material
gray_material = bpy.data.materials.new(name="GrayMat")
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to add a cube with given properties

def add_cube(size, position, object_name, scale_factors, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    new_cube = bpy.context.object
    new_cube.name = object_name
    new_cube.scale = scale_factors
    new_cube.data.materials.append(material)

# Create the base geometry
add_cube(2, (0, 0, 0.1), "BaseGeometry", (1, 0.5, 0.05), gray_material)

# Generate slots for plates
for i in range(5):
    x_coord = -0.9 + i * 0.4
    add_cube(1, (x_coord, 0, 0.35), f"PlateSlot_{i + 1}", (0.1, 0.05, 0.5), gray_material)

# Create a flat area for utensils
add_cube(1, (0, -0.35, 0.1), "UtensilArea", (0.9, 0.4, 0.05), gray_material)


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
