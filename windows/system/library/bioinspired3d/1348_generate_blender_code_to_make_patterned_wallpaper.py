# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_to_make_patterned_wallpaper" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code to make patterned wallpaper.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
mat_light = bpy.data.materials.new(name='Mat Light')
mat_light.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_dark = bpy.data.materials.new(name='Mat Dark')
mat_dark.diffuse_color = (0.2, 0.2, 0.5, 1)

# Create the base plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
base_mesh = bpy.context.object
base_mesh.name = 'Base Plane'
base_mesh.data.materials.append(mat_light)

# Loop through grid coordinates to create cubes and spheres
for x in range(-4, 5):
    for y in range(-4, 5):
        # Create a cube
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 0.25))
        cube_object = bpy.context.object
        cube_object.name = f'Cube_{x}_{y}'
        cube_object.data.materials.append(mat_dark)
        
        # Create a sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(x, y, 0.75))
        sphere_object = bpy.context.object
        sphere_object.name = f'Sphere_{x}_{y}'
        sphere_object.data.materials.append(mat_dark)


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
