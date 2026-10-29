# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_create_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to create wallpaper pattern

import bpy

# Begin by clearing the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define new materials
material_gray = bpy.data.materials.new(name='GrayMaterial')
material_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
material_blue = bpy.data.materials.new(name='BlueMaterial')
material_blue.diffuse_color = (0.2, 0.2, 0.8, 1)

# Create a function to add shapes

def add_shape(shape, coords, rotation, scale_factor, mat):
    if shape == 'cube':
        bpy.ops.mesh.primitive_cube_add(location=coords, rotation=rotation)
    elif shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(location=coords, rotation=rotation)
    elif shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(location=coords, rotation=rotation)
    obj = bpy.context.object
    obj.scale = scale_factor
    obj.data.materials.append(mat)
    return obj

# Create a base plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
plane_object = bpy.context.object
plane_object.name = 'Main Plane'
plane_object.data.materials.append(material_gray)

# Generate shapes in a grid
spacing_value = 2
for x in range(-4, 5, spacing_value):
    for y in range(-4, 5, spacing_value):
        add_shape('cube', (x, y, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), material_blue)
        add_shape('sphere', (x + 1, y + 1, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), material_blue)
        add_shape('cylinder', (x + 1, y, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), material_blue)


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
