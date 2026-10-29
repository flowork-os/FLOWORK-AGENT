# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_to_create_patterned_wallpaper" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code to create patterned wallpaper.

import bpy

# Start by clearing the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the geometry
material_light = bpy.data.materials.new(name='Light Gray')
material_light.diffuse_color = (0.8, 0.8, 0.8, 1)
material_dark = bpy.data.materials.new(name='Dark Blue')
material_dark.diffuse_color = (0.2, 0.2, 0.5, 1)

# Create the base plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
plane_object = bpy.context.object
plane_object.name = 'Base Plane'
plane_object.data.materials.append(material_light)

# Function to create a cube and sphere at a given position
def create_shapes(x, y):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 0.25))
    cube = bpy.context.object
    cube.name = f'Cube_{x}_{y}'
    cube.data.materials.append(material_dark)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(x, y, 0.75))
    sphere = bpy.context.object
    sphere.name = f'Sphere_{x}_{y}'
    sphere.data.materials.append(material_dark)

# Generate the grid of shapes
for x in range(-4, 5):
    for y in range(-4, 5):
        create_shapes(x, y)


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
