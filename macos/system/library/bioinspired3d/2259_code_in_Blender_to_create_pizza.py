# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_create_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to create pizza.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for pizza components
crust_material = bpy.data.materials.new(name="CrustMaterial")
crust_material.diffuse_color = (0.8, 0.6, 0.4, 1)
sauce_material = bpy.data.materials.new(name="SauceMaterial")
sauce_material.diffuse_color = (0.8, 0.1, 0.1, 1)
cheese_material = bpy.data.materials.new(name="CheeseMaterial")
cheese_material.diffuse_color = (1, 0.9, 0.5, 1)
pepperoni_material = bpy.data.materials.new(name="PepperoniMaterial")
pepperoni_material.diffuse_color = (0.7, 0.2, 0.2, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the pizza layers
create_cylinder(1.1, 0.1, (0, 0, 0), "PizzaCrust", crust_material)
create_cylinder(1, 0.02, (0, 0, 0.06), "TomatoSauce", sauce_material)
create_cylinder(0.95, 0.02, (0, 0, 0.08), "CheeseLayer", cheese_material)

# Add pepperoni slices
num_slices = 8
for i in range(num_slices):
    theta = i * (2 * math.pi / num_slices)
    pos_x = 0.7 * math.cos(theta)
    pos_y = 0.7 * math.sin(theta)
    create_cylinder(0.1, 0.02, (pos_x, pos_y, 0.1), f"PepperoniSlice_{i + 1}", pepperoni_material)


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
