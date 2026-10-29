# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_mandala_pattern_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of mandala pattern using blender code

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the mandala
mandala_material = bpy.data.materials.new(name="Mandala Material")
mandala_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Set to medium gray

# Function to create a circle at the center

def create_center_circle():
    bpy.ops.mesh.primitive_circle_add(radius=1, location=(0, 0, 0))
    circle = bpy.context.object
    circle.name = "Center Circle"
    circle.data.materials.append(mandala_material)

# Function to create radiating shapes

def create_radiating_shapes(num_shapes):
    angle_increment = 2 * math.pi / num_shapes
    for i in range(num_shapes):
        angle = i * angle_increment
        x = math.cos(angle) * 2
        y = math.sin(angle) * 2
        bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.1, location=(x, y, 0), rotation=(0, 0, angle))
        shape = bpy.context.object
        shape.name = f"Shape {i + 1}"
        shape.data.materials.append(mandala_material)

# Function to create additional layers

def create_layers(num_layers, num_shapes):
    for layer in range(1, num_layers + 1):
        radius = 2 + layer
        angle_increment = 2 * math.pi / num_shapes
        for i in range(num_shapes):
            angle = i * angle_increment
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(x, y, 0), rotation=(0, 0, angle))
            torus = bpy.context.object
            torus.name = f"Torus Layer {layer} Shape {i + 1}"
            torus.data.materials.append(mandala_material)

# Execute the functions
create_center_circle()
create_radiating_shapes(12)
create_layers(3, 12)


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
