# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_make_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to make sofa

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_color_material = bpy.data.materials.new(name="SofaColorMaterial")
sofa_color_material.diffuse_color = (0.5, 0.25, 0.1, 1)

# Method to generate a sofa component
def generate_sofa_part(part_size, part_location, part_name, part_scale, part_material):
    bpy.ops.mesh.primitive_cube_add(size=part_size, location=part_location)
    part = bpy.context.object
    part.name = part_name
    part.scale = part_scale
    part.data.materials.append(part_material)

# Sofa base
generate_sofa_part(2, (0, 0, 0.5), "Sofa_Base", (3, 1, 0.5), sofa_color_material)

# Backrest
generate_sofa_part(2, (0, -0.95, 1.25), "Backrest", (3, 0.1, 0.75), sofa_color_material)

# Armrests
for i in range(2):
    armrest_position = 3 * (i * 2 - 1)
    generate_sofa_part(2, (armrest_position, 0, 0.75), f"Armrest_{i + 1}", (0.1, 1, 0.75), sofa_color_material)

# Storage
generate_sofa_part(2, (0, 0, -0.25), "Storage", (3, 1, 0.25), sofa_color_material)


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
