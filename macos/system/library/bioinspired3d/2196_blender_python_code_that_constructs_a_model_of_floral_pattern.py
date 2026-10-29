# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_constructs_a_model_of_floral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that constructs a model of floral pattern.

import bpy
import math

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the flower and the surface
flower_material = bpy.data.materials.new(name='Flower Material')
flower_material.diffuse_color = (1, 0, 0, 1)  # Red
surface_material = bpy.data.materials.new(name='Surface Material')
surface_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray

# Function to create a flower at a given location
def add_flower(location):
    x, y, z = location
    # Create the center of the flower
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(x, y, z))
    flower_center = bpy.context.object
    flower_center.name = 'Flower Center'
    flower_center.data.materials.append(flower_material)
    
    # Create petals around the center
    num_petals = 5
    petal_distance = 0.3
    for i in range(num_petals):
        theta = i * (2 * math.pi / num_petals)
        petal_x = x + petal_distance * math.cos(theta)
        petal_y = y + petal_distance * math.sin(theta)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(petal_x, petal_y, z))
        petal = bpy.context.object
        petal.name = f'Petal {i + 1}'
        petal.data.materials.append(flower_material)

# Create the circular surface
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=0.1, location=(0, 0, 0))
surface = bpy.context.object
surface.name = 'Surface'
surface.data.materials.append(surface_material)

# List of flower positions
flower_positions = [(-1, -1, 0.05), (1, -1, 0.05), (-1, 1, 0.05), (1, 1, 0.05), (0, 0, 0.05)]
for position in flower_positions:
    add_flower(position)


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
