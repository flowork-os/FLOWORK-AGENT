# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_create_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to create pizza

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
crust_material = bpy.data.materials.new(name='CrustMaterial')
crust_material.diffuse_color = (0.76, 0.60, 0.42, 1)
cheese_material = bpy.data.materials.new(name='CheeseMaterial')
cheese_material.diffuse_color = (1.0, 0.9, 0.4, 1)
pepperoni_material = bpy.data.materials.new(name='PepperoniMaterial')
pepperoni_material.diffuse_color = (0.8, 0.1, 0.1, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the crust
create_cylinder(1.5, 0.1, (0, 0, 0), 'Crust', crust_material)

# Create the cheese layer
create_cylinder(1.4, 0.02, (0, 0, 0.06), 'Cheese', cheese_material)

# Define pepperoni positions
pepperoni_locations = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5)]
for index, location in enumerate(pepperoni_locations):
    create_cylinder(0.2, 0.02, (location[0], location[1], 0.08), f'Pepperoni_{index + 1}', pepperoni_material)


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
