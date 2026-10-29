# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_building_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for building a model of sofa

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Sofa material definition
material_for_sofa = bpy.data.materials.new(name="Material for Sofa")
material_for_sofa.diffuse_color = (0.2, 0.2, 0.2, 1)  # Color: Dark gray

# Function to add a cube with given attributes
def add_cube(name, loc, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    cube = bpy.context.object
    cube.name = name
    cube.scale = dimensions
    cube.data.materials.append(material_for_sofa)

# Constructing the seat
add_cube("Seat", (0, 0, 0.5), (3, 1, 0.5))

# Constructing the backrest
add_cube("Backrest", (0, -1, 1.25), (3, 0.2, 1))

# Constructing the armrests
for index in range(2):
    x_position = 3 * (index * 2 - 1)
    add_cube(f"Armrest {index + 1}", (x_position, 0, 0.75), (0.2, 1, 0.75))


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
