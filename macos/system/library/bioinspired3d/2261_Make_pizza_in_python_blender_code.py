# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_pizza_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make pizza in python blender code

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for pizza components
materials = [
    ("PizzaCrust", (0.8, 0.6, 0.4, 1)),
    ("TomatoSauce", (0.8, 0.1, 0.1, 1)),
    ("CheeseLayer", (1, 0.9, 0.5, 1)),
    ("PepperoniSlice", (0.7, 0.2, 0.2, 1))
]

# Function to add a material
def add_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Assign materials
material_objects = [add_material(name, color) for name, color in materials]

# Create pizza geometry
bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.1, location=(0, 0, 0))
crust = bpy.context.object
crust.data.materials.append(material_objects[0])

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.02, location=(0, 0, 0.06))
sauce = bpy.context.object
sauce.data.materials.append(material_objects[1])

bpy.ops.mesh.primitive_cylinder_add(radius=0.95, depth=0.02, location=(0, 0, 0.08))
cheese = bpy.context.object
cheese.data.materials.append(material_objects[2])

# Create pepperoni slices in a circular pattern
for i in range(8):
    angle = i * (math.pi / 4)
    x = 0.7 * math.cos(angle)
    y = 0.7 * math.sin(angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.02, location=(x, y, 0.1))
    pepperoni = bpy.context.object
    pepperoni.data.materials.append(material_objects[3])
    pepperoni.name = f"Pepperoni_{i + 1}"


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
