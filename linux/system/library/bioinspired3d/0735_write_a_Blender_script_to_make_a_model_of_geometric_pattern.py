# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_to_make_a_model_of_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script to make a model of geometric pattern.

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define shades of blue
blue_colors = [
    (0.1, 0.1, 0.5, 1),  # Dark blue
    (0.2, 0.2, 0.6, 1),  # Medium dark blue
    (0.3, 0.3, 0.7, 1),  # Medium blue
    (0.4, 0.4, 0.8, 1),  # Medium light blue
    (0.5, 0.5, 0.9, 1)   # Light blue
]

# Create materials for shapes
material_array = [bpy.data.materials.new(name=f"Blue Material {i + 1}") for i, color in enumerate(blue_colors)]
for mat, color in zip(material_array, blue_colors):
    mat.diffuse_color = color

# Hexagon class to manage hexagon creation
class Hexagon:
    def __init__(self, radius, location, material):
        self.radius = radius
        self.location = location
        self.material = material
        self.create_hexagon()

    def create_hexagon(self):
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=self.radius, location=self.location, fill_type='NGON')
        hex_object = bpy.context.object
        hex_object.data.materials.append(self.material)

# Function to create a triangle
def create_triangle(length, position, rotation, material):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=length / math.sqrt(3), location=position, rotation=rotation, fill_type='NGON')
    triangle = bpy.context.object
    triangle.data.materials.append(material)

# Grid parameters
num_rows = 5
num_cols = 5
hex_radius = 1
tri_length = hex_radius * math.sqrt(3)

# Generate grid of hexagons and triangles
for row in range(num_rows):
    for col in range(num_cols):
        x_offset = col * 1.5 * hex_radius
        y_offset = row * math.sqrt(3) * hex_radius
        if col % 2 == 1:
            y_offset += math.sqrt(3) * hex_radius / 2
        
        # Create hexagon
        hex_material = material_array[(row + col) % len(material_array)]
        Hexagon(hex_radius, (x_offset, y_offset, 0), hex_material)
        
        # Create surrounding triangles
        for i in range(6):
            angle = math.radians(60 * i)
            tri_x = x_offset + hex_radius * math.cos(angle)
            tri_y = y_offset + hex_radius * math.sin(angle)
            tri_rotation = (0, 0, angle + math.radians(30))
            tri_material = material_array[(row + col + 1) % len(material_array)]
            create_triangle(tri_length, (tri_x, tri_y, 0), tri_rotation, tri_material)


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
