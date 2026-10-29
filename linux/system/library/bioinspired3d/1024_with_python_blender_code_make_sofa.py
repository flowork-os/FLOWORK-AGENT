# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code_make_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code make sofa.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sofa
material_sofa = bpy.data.materials.new(name="MaterialSofa")
material_sofa.diffuse_color = (0.5, 0.25, 0.25, 1)
material_cushion = bpy.data.materials.new(name="MaterialCushion")
material_cushion.diffuse_color = (0.75, 0.75, 0.75, 1)

# Function to add a cube with material

def add_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)

# Create sofa base
add_cube(2, (0, 0, 0.5), (2, 1, 0.5), "Sofa Base", material_sofa)

# Create backrest
add_cube(2, (0, -0.75, 1.25), (2, 0.25, 0.75), "Backrest", material_sofa)

# Create seat cushions
for i in range(3):
    position = (i - 1) * 1.3
    add_cube(1, (position, 0, 1), (0.6, 0.9, 0.2), f"Seat Cushion {i + 1}", material_cushion)

# Create backrest cushions
for i in range(3):
    position = (i - 1) * 1.3
    add_cube(1, (position, -0.75, 1.75), (0.6, 0.2, 0.6), f"Backrest Cushion {i + 1}", material_cushion)


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
