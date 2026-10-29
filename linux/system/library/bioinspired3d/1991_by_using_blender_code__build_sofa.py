# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code__build_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code, build sofa.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_texture = bpy.data.materials.new(name="SofaTexture")
sofa_texture.diffuse_color = (0.5, 0.25, 0.1, 1)

# Create the sofa components using functions
def add_sofa_component(shape, position, title, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(size=shape, location=position)
    component = bpy.context.object
    component.name = title
    component.scale = dimensions
    component.data.materials.append(mat)

# Sofa base
add_sofa_component(2, (0, 0, 0.5), "Base", (3, 1, 0.5), sofa_texture)

# Backrest
add_sofa_component(2, (0, -0.95, 1.25), "Backrest", (3, 0.1, 0.75), sofa_texture)

# Armrests
for index in range(2):
    position_x = 3 * (index * 2 - 1)
    add_sofa_component(2, (position_x, 0, 0.75), f"Armrest {index + 1}", (0.1, 1, 0.75), sofa_texture)

# Storage area
add_sofa_component(2, (0, 0, -0.25), "Storage Area", (3, 1, 0.25), sofa_texture)


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
