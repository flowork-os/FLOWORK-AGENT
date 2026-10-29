# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_floral_pattern_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct floral pattern in python blender code

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the flower and surface
flower_material = bpy.data.materials.new(name='Flower Material')
flower_material.diffuse_color = (1, 0, 0, 1)  # Bright red
surface_material = bpy.data.materials.new(name='Surface Material')
surface_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Soft gray

# Function to generate flowers
def generate_flower(position):
    x, y, z = position
    # Add flower center
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(x, y, z))
    center = bpy.context.object
    center.name = 'Flower Center'
    center.data.materials.append(flower_material)
    
    # Add petals around the center
    petals_count = 5
    petal_distance = 0.3
    for i in range(petals_count):
        angle = i * (2 * math.pi / petals_count)
        petal_x = x + petal_distance * math.cos(angle)
        petal_y = y + petal_distance * math.sin(angle)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(petal_x, petal_y, z))
        petal = bpy.context.object
        petal.name = f'Petal {i + 1}'
        petal.data.materials.append(flower_material)

# Create the circular surface
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=0.1, location=(0, 0, 0))
surface = bpy.context.object
surface.name = 'Surface'
surface.data.materials.append(surface_material)

# Define flower positions
flower_positions = [(-1, -1, 0.05), (1, -1, 0.05), (-1, 1, 0.05), (1, 1, 0.05), (0, 0, 0.05)]
for position in flower_positions:
    generate_flower(position)


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
