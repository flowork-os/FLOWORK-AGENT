# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_making_a_model_of_pet_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for making a model of pet bed.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bed and cushion
bed_material = bpy.data.materials.new(name='Bed Material')
bed_material.diffuse_color = (0.5, 0.25, 0.2, 1)  # Darker brown
cushion_material = bpy.data.materials.new(name='Cushion Material')
cushion_material.diffuse_color = (0.9, 0.9, 0.9, 1)  # Slightly lighter gray

# Function to create a cube
def add_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)

# Create the bed base
add_cube(2, (0, 0, 0.25), (1, 1.5, 0.1), 'Bed Base', bed_material)

# Create the sides of the bed
add_cube(2, (0, -1.5, 0.75), (1, 0.1, 0.5), 'Front Side', bed_material)
add_cube(2, (0, 1.5, 0.75), (1, 0.1, 0.5), 'Back Side', bed_material)
add_cube(2, (-1, 0, 0.75), (0.1, 1.5, 0.5), 'Left Side', bed_material)
add_cube(2, (1, 0, 0.75), (0.1, 1.5, 0.5), 'Right Side', bed_material)

# Create the cushion
add_cube(2, (0, 0, 0.35), (0.9, 1.4, 0.05), 'Cushion', cushion_material)


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
