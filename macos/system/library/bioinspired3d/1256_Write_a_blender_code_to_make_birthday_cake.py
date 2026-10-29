# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_to_make_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code to make birthday cake.

import bpy
import random

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a white material for the cake frosting
frosting_material = bpy.data.materials.new(name='Frosting Material')
frosting_material.diffuse_color = (1, 1, 1, 1)

# Define colors for the sprinkles
colors = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0, 1, 1),  # Magenta
    (0, 1, 1, 1)   # Cyan
]

# Create the cake layers using a loop
heights = [0.3, 0.25, 0.2]
radii = [1, 0.85, 0.7]
for index in range(len(heights)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radii[index], depth=heights[index], location=(0, 0, sum(heights[:index]) + heights[index] / 2))
    layer = bpy.context.object
    layer.name = f'Cake Layer {index + 1}'
    layer.data.materials.append(frosting_material)

# Function to add sprinkles to the top layer of the cake
def add_sprinkles(num_sprinkles):
    top_z = sum(heights) + 0.02
    for _ in range(num_sprinkles):
        x_pos = random.uniform(-radii[2], radii[2])
        y_pos = random.uniform(-radii[2], radii[2])
        if x_pos**2 + y_pos**2 <= radii[2]**2:
            sprinkle_color = random.choice(colors)
            create_sprinkle((x_pos, y_pos, top_z), sprinkle_color)

# Function to create individual sprinkles
def create_sprinkle(location, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=location)
    sprinkle = bpy.context.object
    sprinkle_material = bpy.data.materials.new(name='Sprinkle')
    sprinkle_material.diffuse_color = color
    sprinkle.data.materials.append(sprinkle_material)

# Add 50 sprinkles on top of the cake
add_sprinkles(50)


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
