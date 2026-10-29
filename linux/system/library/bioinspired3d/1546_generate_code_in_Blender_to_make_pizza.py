# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_to_make_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender to make pizza

import bpy

# Clear the existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the pizza components
crust_material = bpy.data.materials.new(name='CrustMaterial')
crust_material.diffuse_color = (0.8, 0.5, 0.2, 1)
cheese_material = bpy.data.materials.new(name='CheeseMaterial')
cheese_material.diffuse_color = (1, 0.9, 0.5, 1)

# Function to create a cylinder with a specific radius, depth, and location
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Add the crust and cheese layers
crust_layer = create_cylinder(1.1, 0.1, (0, 0, 0), 'PizzaCrust', crust_material)
cheese_layer = create_cylinder(1, 0.02, (0, 0, 0.06), 'PizzaCheese', cheese_material)


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
