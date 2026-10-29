# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_wallpaper_pattern_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of wallpaper pattern using blender python code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the objects
light_gray_material = bpy.data.materials.new(name='LightGray')
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)
blue_material = bpy.data.materials.new(name='Blue')
blue_material.diffuse_color = (0.2, 0.2, 0.8, 1)

# Function to generate a geometric shape
def generate_shape(shape_type, position, rotation_angles, scaling_factors, mat):
    if shape_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(location=position, rotation=rotation_angles)
    elif shape_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(location=position, rotation=rotation_angles)
    elif shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(location=position, rotation=rotation_angles)
    shape_object = bpy.context.object
    shape_object.scale = scaling_factors
    shape_object.data.materials.append(mat)
    return shape_object

# Create a base plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
base_plane = bpy.context.object
base_plane.name = 'Ground Plane'
base_plane.data.materials.append(light_gray_material)

# Arrange shapes in a grid layout
spacing_distance = 2
for x in range(-4, 5, spacing_distance):
    for y in range(-4, 5, spacing_distance):
        generate_shape('cube', (x, y, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), blue_material)
        generate_shape('sphere', (x + 1, y + 1, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), blue_material)
        generate_shape('cylinder', (x + 1, y, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), blue_material)


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
