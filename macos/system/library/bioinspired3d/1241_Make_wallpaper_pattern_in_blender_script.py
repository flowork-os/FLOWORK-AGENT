# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_wallpaper_pattern_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make wallpaper pattern in blender script

import bpy

# Clear the current mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for shapes
mat_light_gray = bpy.data.materials.new(name='LightGrayMaterial')
mat_light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_dark_blue = bpy.data.materials.new(name='DarkBlueMaterial')
mat_dark_blue.diffuse_color = (0.2, 0.2, 0.8, 1)

# Function to create a geometric shape

def create_geometric_shape(shape_name, pos, rot, scale_factor, material):
    if shape_name == 'cube':
        bpy.ops.mesh.primitive_cube_add(location=pos, rotation=rot)
    elif shape_name == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(location=pos, rotation=rot)
    elif shape_name == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(location=pos, rotation=rot)
    shape_instance = bpy.context.object
    shape_instance.scale = scale_factor
    shape_instance.data.materials.append(material)
    return shape_instance

# Create a base plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
base_shape = bpy.context.object
base_shape.name = 'Ground'
base_shape.data.materials.append(mat_light_gray)

# Create a grid of shapes
spacing = 2
for x in range(-4, 5, spacing):
    for y in range(-4, 5, spacing):
        create_geometric_shape('cube', (x, y, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), mat_dark_blue)
        create_geometric_shape('sphere', (x + 1, y + 1, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), mat_dark_blue)
        create_geometric_shape('cylinder', (x + 1, y, 0.5), (0, 0, 0), (0.5, 0.5, 0.5), mat_dark_blue)


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
