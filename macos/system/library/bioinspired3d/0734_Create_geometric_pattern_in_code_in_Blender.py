# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_geometric_pattern_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create geometric pattern in code in Blender

import bpy
import math

# Step 1: Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define color palette for materials
color_palette = [
    (0.1, 0.1, 0.5, 1),  # Dark blue
    (0.2, 0.2, 0.6, 1),  # Medium dark blue
    (0.3, 0.3, 0.7, 1),  # Medium blue
    (0.4, 0.4, 0.8, 1),  # Medium light blue
    (0.5, 0.5, 0.9, 1)   # Light blue
]

# Create materials from color palette
material_list = []
for index, shade in enumerate(color_palette):
    material = bpy.data.materials.new(name=f"Material {index + 1}")
    material.diffuse_color = shade
    material_list.append(material)

# Function to generate a hexagonal shape
def generate_hexagon(size, position, mat):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=size, location=position, fill_type='NGON')
    hex_shape = bpy.context.object
    hex_shape.data.materials.append(mat)
    return hex_shape

# Function to generate a triangular shape
def generate_triangle(length, position, orient, mat):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=length / math.sqrt(3), location=position, rotation=orient, fill_type='NGON')
    tri_shape = bpy.context.object
    tri_shape.data.materials.append(mat)
    return tri_shape

# Configuration for hexagon and triangle dimensions
hexagon_size = 1  # Hexagon radius
triangle_length = hexagon_size * math.sqrt(3)  # Triangle side length

# Create the grid pattern
grid_rows = 5
grid_cols = 5
for row in range(grid_rows):
    for col in range(grid_cols):
        x_shift = col * 1.5 * hexagon_size
        y_shift = row * math.sqrt(3) * hexagon_size
        if col % 2 == 1:
            y_shift += math.sqrt(3) * hexagon_size / 2
        
        # Create hexagon
        hex_material = material_list[(row + col) % len(material_list)]
        generate_hexagon(hexagon_size, (x_shift, y_shift, 0), hex_material)
        
        # Create surrounding triangles
        for i in range(6):
            angle_offset = math.radians(60 * i)
            triangle_x = x_shift + hexagon_size * math.cos(angle_offset)
            triangle_y = y_shift + hexagon_size * math.sin(angle_offset)
            triangle_orientation = (0, 0, angle_offset + math.radians(30))
            triangle_material = material_list[(row + col + 1) % len(material_list)]
            generate_triangle(triangle_length, (triangle_x, triangle_y, 0), triangle_orientation, triangle_material)


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
