# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_sofa_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make sofa using blender python code

import bpy

# Remove all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize the sofa material
material_sofa = bpy.data.materials.new(name="Material Sofa")
material_sofa.diffuse_color = (0.5, 0.25, 0.25, 1)  # Dark reddish-brown

# Generate the main parts of the sofa

def add_sofa_part(part_name, coords, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=2, location=coords)
    part = bpy.context.object
    part.scale[0], part.scale[1], part.scale[2] = dimensions
    part.name = part_name
    part.data.materials.append(material_sofa)

# Create the seat and backrest
add_sofa_part("Seat", (0, 0, 0.5), (2, 1, 0.2))
add_sofa_part("Backrest", (0, -0.9, 1.1), (2, 0.2, 0.6))

# Create armrests on both sides
for i in range(2):
    pos = (2 * (i * 2 - 1), 0, 0.9)
    add_sofa_part(f"Armrest {i + 1}", pos, (0.2, 1, 0.4))


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
