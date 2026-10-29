# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code__build_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code, build puzzle cube

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color definitions for materials
palette = {
    "white": (1, 1, 1, 1),
    "yellow": (1, 1, 0, 1),
    "red": (1, 0, 0, 1),
    "orange": (1, 0.5, 0, 1),
    "blue": (0, 0, 1, 1),
    "green": (0, 1, 0, 1)
}

# Function to create materials from a color palette
def create_materials(color_dict):
    mats = {}
    for name, value in color_dict.items():
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = value
        mats[name] = mat
    return mats

# Create materials
material_list = create_materials(palette)

# Size and spacing for cubes
cube_dimension = 0.95
spacing = 0.05

# Create a grid of cubes
for x in range(3):
    for y in range(3):
        for z in range(3):
            bpy.ops.mesh.primitive_cube_add(size=cube_dimension, location=(x * (cube_dimension + spacing), y * (cube_dimension + spacing), z * (cube_dimension + spacing)))
            cube_object = bpy.context.object
            cube_object.name = f"Cube_{x}_{y}_{z}"
            # Assign materials to cube faces
            for face_index in range(6):
                face = cube_object.data.polygons[face_index]
                face.material_index = face_index % len(material_list)
                cube_object.data.materials.append(material_list[list(material_list.keys())[face_index % len(material_list)]])


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
