# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_building_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for building a model of pizza

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for pizza layers
material_crust = bpy.data.materials.new(name='PizzaCrustMaterial')
material_crust.diffuse_color = (0.8, 0.5, 0.2, 1)
material_cheese = bpy.data.materials.new(name='PizzaCheeseMaterial')
material_cheese.diffuse_color = (1, 0.9, 0.5, 1)

# Create the crust
bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.1, location=(0, 0, 0))
crust_object = bpy.context.object
crust_object.name = 'CrustLayer'
crust_object.data.materials.append(material_crust)

# Create the cheese layer
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.02, location=(0, 0, 0.06))
cheese_object = bpy.context.object
cheese_object.name = 'CheeseLayer'
cheese_object.data.materials.append(material_cheese)


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
