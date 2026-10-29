# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_model_of_patterned_wallpaper" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a model of patterned wallpaper.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
light_material = bpy.data.materials.new(name='Light Material')
light_material.diffuse_color = (0.8, 0.8, 0.8, 1)
dark_material = bpy.data.materials.new(name='Dark Material')
dark_material.diffuse_color = (0.2, 0.2, 0.5, 1)

# Function to add cubes and spheres
def add_geometric_shapes(x, y):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 0.25))
    cube = bpy.context.object
    cube.name = f'Cube_{x}_{y}'
    cube.data.materials.append(dark_material)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(x, y, 0.75))
    sphere = bpy.context.object
    sphere.name = f'Sphere_{x}_{y}'
    sphere.data.materials.append(dark_material)

# Create the base plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
base_surface = bpy.context.object
base_surface.name = 'Base Plane'
base_surface.data.materials.append(light_material)

# Generate the geometric pattern
for x in range(-4, 5):
    for y in range(-4, 5):
        add_geometric_shapes(x, y)


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
