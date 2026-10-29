# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_hat_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of hat in blender python code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the hat
brown_material = bpy.data.materials.new(name='BrownMaterial')
brown_material.diffuse_color = (0.5, 0.25, 0.1, 1)

black_material = bpy.data.materials.new(name='BlackMaterial')
black_material.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to add a hat component
def add_hat_component(shape, radius, depth, position, name, material):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    elif shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create brim, crown, and band
brim = add_hat_component('cylinder', 1.5, 0.1, (0, 0, 0), 'Brim', brown_material)
crown = add_hat_component('sphere', 0.75, None, (0, 0, 0.5), 'Crown', brown_material)
band = add_hat_component('cylinder', 0.85, 0.2, (0, 0, 0.3), 'Band', black_material)


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
