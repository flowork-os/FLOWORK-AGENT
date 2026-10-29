# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_makes_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that makes pizza

import bpy
import math

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
materials = {
    'Crust': (0.76, 0.60, 0.42, 1),
    'Sauce': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.9, 0.5, 1),
    'Pepperoni': (0.6, 0.1, 0.1, 1)
}

# Function to create materials
def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create materials
crust_mat = create_material("Crust Material", materials['Crust'])
sauce_mat = create_material("Sauce Material", materials['Sauce'])
cheese_mat = create_material("Cheese Material", materials['Cheese'])
pepperoni_mat = create_material("Pepperoni Material", materials['Pepperoni'])

# Function to add a cylinder
def add_cylinder(radius, depth, pos, mat, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)

# Create pizza components
add_cylinder(1, 0.1, (0, 0, 0), crust_mat, "Pizza Base")
add_cylinder(0.95, 0.02, (0, 0, 0.06), sauce_mat, "Sauce Layer")
add_cylinder(0.9, 0.02, (0, 0, 0.08), cheese_mat, "Cheese Layer")

# Pepperoni slice positions
positions = [
    (0.3, 0.3), (-0.3, 0.3), (0.3, -0.3), (-0.3, -0.3),
    (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6)
]

# Adding pepperoni slices
for idx, pos in enumerate(positions):
    add_cylinder(0.1, 0.02, (pos[0], pos[1], 0.1), pepperoni_mat, f"Pepperoni {idx + 1}")

# Cutting the pizza into slices
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["Pizza Base"]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1, radius2=0, depth=0.2, location=(0, 0, 0.1), rotation=(0, 0, math.pi / 8))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.object.select_set(True)
bpy.ops.object.join()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.intersect_boolean(operation='DIFFERENCE')
bpy.ops.object.mode_set(mode='OBJECT')


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
