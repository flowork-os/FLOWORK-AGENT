# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_birthday_cake_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct birthday cake using python blender code

import bpy
import random

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize the frosting material
cake_frosting = bpy.data.materials.new(name='Cake Frosting')
cake_frosting.diffuse_color = (1, 1, 1, 1)

# List of colors for sprinkles
sprinkle_list = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0, 1, 1),  # Magenta
    (0, 1, 1, 1)   # Cyan
]

# Function to build the cake
class Cake:
    def __init__(self, heights, radii):
        self.heights = heights
        self.radii = radii
        self.create_layers()

    def create_layers(self):
        current_height = 0
        for index in range(len(self.heights)):
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radii[index], depth=self.heights[index], location=(0, 0, current_height + self.heights[index] / 2))
            layer = bpy.context.object
            layer.name = f'Layer {index + 1}'
            layer.data.materials.append(cake_frosting)
            current_height += self.heights[index]

# Create the cake layers
cake_heights = [0.3, 0.25, 0.2]
cake_radii = [1, 0.85, 0.7]
cake = Cake(cake_heights, cake_radii)

# Function to place sprinkles
def place_sprinkles(num_sprinkles):
    top_layer_z = sum(cake_heights) + 0.02
    for _ in range(num_sprinkles):
        x_pos = random.uniform(-cake_radii[2], cake_radii[2])
        y_pos = random.uniform(-cake_radii[2], cake_radii[2])
        if x_pos**2 + y_pos**2 <= cake_radii[2]**2:
            sprinkle_color = random.choice(sprinkle_list)
            create_sprinkle((x_pos, y_pos, top_layer_z), sprinkle_color)

# Function to create a single sprinkle
def create_sprinkle(location, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=location)
    sprinkle = bpy.context.object
    sprinkle_material = bpy.data.materials.new(name='Sprinkle Material')
    sprinkle_material.diffuse_color = color
    sprinkle.data.materials.append(sprinkle_material)

# Add sprinkles to the top layer
place_sprinkles(50)


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
