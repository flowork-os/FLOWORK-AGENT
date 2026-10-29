# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_to_create_floral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script to create floral pattern.

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the flower components
petal_material = bpy.data.materials.new(name="Petal Material")
petal_material.diffuse_color = (1, 0.5, 0.5, 1)

center_material = bpy.data.materials.new(name="Center Material")
center_material.diffuse_color = (1, 1, 0, 1)

# Function to generate a flower at a specific location
def generate_flower(position):
    # Generate petals in a circular arrangement
    for index in range(5):
        theta = index * (2 * math.pi / 5)
        x_offset = 0.2 * math.cos(theta)
        y_offset = 0.2 * math.sin(theta)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(position[0] + x_offset, position[1] + y_offset, position[2]))
        petal_object = bpy.context.object
        petal_object.data.materials.append(petal_material)
    
    # Create the flower center
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=position)
    center_object = bpy.context.object
    center_object.data.materials.append(center_material)

# Arrange flowers in a grid pattern
num_rows = 5
num_cols = 5
flower_spacing = 1.0

for row in range(num_rows):
    for col in range(num_cols):
        generate_flower((row * flower_spacing, col * flower_spacing, 0))


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
