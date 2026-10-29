# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making birthday cake.

import bpy
import random

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a white frosting material
frosting_material = bpy.data.materials.new(name='Frosting')
frosting_material.diffuse_color = (1, 1, 1, 1)

# Define the colors for sprinkles
sprinkle_palette = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0, 1, 1),  # Magenta
    (0, 1, 1, 1)   # Cyan
]

# Function to create cake layers
def create_cake_layers(heights, radii):
    total_height = 0
    for idx in range(len(heights)):
        bpy.ops.mesh.primitive_cylinder_add(radius=radii[idx], depth=heights[idx], location=(0, 0, total_height + heights[idx] / 2))
        layer = bpy.context.object
        layer.name = f'Cake Layer {idx + 1}'
        layer.data.materials.append(frosting_material)
        total_height += heights[idx]

# Create cake layers with specified heights and radii
layer_heights = [0.3, 0.25, 0.2]
layer_radii = [1, 0.85, 0.7]
create_cake_layers(layer_heights, layer_radii)

# Function to generate a sprinkle
def generate_sprinkle(position, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=position)
    sprinkle = bpy.context.object
    sprinkle_color = bpy.data.materials.new(name='Sprinkle')
    sprinkle_color.diffuse_color = color
    sprinkle.data.materials.append(sprinkle_color)

# Add sprinkles on the top layer
for _ in range(50):
    x_coord = random.uniform(-layer_radii[2], layer_radii[2])
    y_coord = random.uniform(-layer_radii[2], layer_radii[2])
    if x_coord**2 + y_coord**2 <= layer_radii[2]**2:
        z_coord = sum(layer_heights) + 0.02
        sprinkle_color = random.choice(sprinkle_palette)
        generate_sprinkle((x_coord, y_coord, z_coord), sprinkle_color)


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
