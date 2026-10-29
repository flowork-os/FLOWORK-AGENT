# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_flower_pattern_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of flower pattern using a Blender code

import bpy
import math

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the flower components
petal_material = bpy.data.materials.new(name="Petal Material")
petal_material.diffuse_color = (1, 0, 0, 1)  # Bright red
center_material = bpy.data.materials.new(name="Center Material")
center_material.diffuse_color = (1, 1, 0, 1)  # Vivid yellow

# Function to generate a flower at a specified position
def generate_flower(position):
    # Add the center sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=position)
    center_sphere = bpy.context.object
    center_sphere.name = "Flower Center"
    center_sphere.data.materials.append(center_material)
    
    # Create petals around the center
    for index in range(5):
        petal_angle = index * (2 * math.pi / 5)
        petal_x = position[0] + 0.3 * math.cos(petal_angle)
        petal_y = position[1] + 0.3 * math.sin(petal_angle)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(petal_x, petal_y, position[2]))
        petal_sphere = bpy.context.object
        petal_sphere.name = f"Petal {index + 1}"
        petal_sphere.data.materials.append(petal_material)

# Define positions for multiple flowers
flower_positions = [(0, 0, 0), (1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0)]
for pos in flower_positions:
    generate_flower(pos)


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
