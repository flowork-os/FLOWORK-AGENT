# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_makes_a_model_of_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that makes a model of geometric pattern.

import bpy
import math

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color definitions for materials
color_definitions = [
    (0.1, 0.1, 0.5, 1),  # Dark blue
    (0.2, 0.2, 0.6, 1),  # Medium dark blue
    (0.3, 0.3, 0.7, 1),  # Medium blue
    (0.4, 0.4, 0.8, 1),  # Medium light blue
    (0.5, 0.5, 0.9, 1)   # Light blue
]

# Create materials based on color definitions
material_list = []
for index, color in enumerate(color_definitions):
    material = bpy.data.materials.new(name=f"Color Material {index + 1}")
    material.diffuse_color = color
    material_list.append(material)

# Function to add a hexagon
def add_hexagon(radius, location, material):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=radius, location=location, fill_type='NGON')
    hex_object = bpy.context.object
    hex_object.data.materials.append(material)
    return hex_object

# Function to add a triangle
def add_triangle(side_length, location, rotation, material):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=side_length / math.sqrt(3), location=location, rotation=rotation, fill_type='NGON')
    triangle_object = bpy.context.object
    triangle_object.data.materials.append(material)
    return triangle_object

# Parameters for hexagon and triangle dimensions
hexagon_radius = 1  # Hexagon radius
triangle_side_length = hexagon_radius * math.sqrt(3)  # Triangle side length

# Create the grid
grid_height = 5
grid_width = 5
for row in range(grid_height):
    for col in range(grid_width):
        x_offset = col * 1.5 * hexagon_radius
        y_offset = row * math.sqrt(3) * hexagon_radius
        if col % 2 == 1:
            y_offset += math.sqrt(3) * hexagon_radius / 2
        
        # Create hexagon
        hex_material = material_list[(row + col) % len(material_list)]
        add_hexagon(hexagon_radius, (x_offset, y_offset, 0), hex_material)
        
        # Create triangles around the hexagon
        for i in range(6):
            angle = math.radians(60 * i)
            tri_x = x_offset + hexagon_radius * math.cos(angle)
            tri_y = y_offset + hexagon_radius * math.sin(angle)
            tri_rotation = (0, 0, angle + math.radians(30))
            tri_material = material_list[(row + col + 1) % len(material_list)]
            add_triangle(triangle_side_length, (tri_x, tri_y, 0), tri_rotation, tri_material)


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
