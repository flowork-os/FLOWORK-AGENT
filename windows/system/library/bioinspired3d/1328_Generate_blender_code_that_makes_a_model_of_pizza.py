# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_makes_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that makes a model of pizza

import bpy
import math

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define pizza materials
materials = {
    'crust': (0.8, 0.6, 0.4, 1),
    'sauce': (0.8, 0.1, 0.1, 1),
    'cheese': (1, 0.9, 0.5, 1),
    'pepperoni': (0.7, 0.2, 0.2, 1)
}

for name, color in materials.items():
    mat = bpy.data.materials.new(name=f"{name.capitalize()}Material")
    mat.diffuse_color = color

# Create pizza components
bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.1, location=(0, 0, 0))
crust = bpy.context.object
crust.data.materials.append(bpy.data.materials.get("CrustMaterial"))

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.02, location=(0, 0, 0.06))
sauce = bpy.context.object
sauce.data.materials.append(bpy.data.materials.get("SauceMaterial"))

bpy.ops.mesh.primitive_cylinder_add(radius=0.95, depth=0.02, location=(0, 0, 0.08))
cheese = bpy.context.object
cheese.data.materials.append(bpy.data.materials.get("CheeseMaterial"))

# Generate pepperoni slices
for i in range(8):
    angle = i * (math.pi / 4)
    x_pos = 0.7 * math.cos(angle)
    y_pos = 0.7 * math.sin(angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.02, location=(x_pos, y_pos, 0.1))
    pepperoni = bpy.context.object
    pepperoni.data.materials.append(bpy.data.materials.get("PepperoniMaterial"))
    pepperoni.name = f"Slice_{i + 1}"


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
