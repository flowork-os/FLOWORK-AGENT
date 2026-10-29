# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_generates_a_model_of_sunglasses_case_outlook" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that generates a model of sunglasses case outlook

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the case
material_case = bpy.data.materials.new(name='Material Case')
material_case.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray

# Function to create a scaled sphere

def create_sphere(radius, location, scale, name):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    sphere = bpy.context.object
    sphere.name = name
    sphere.scale = scale
    sphere.data.materials.append(material_case)
    return sphere

# Create the main body of the case
main_body = create_sphere(1, (0, 0, 0), (2, 1, 0.5), 'Main Body')

# Create the bottom part of the case
bottom_part = create_sphere(1, (0, 0, -0.5), (2, 1, 0.25), 'Bottom Part')

# Join the two parts into one object
bpy.ops.object.select_all(action='DESELECT')
main_body.select_set(True)
bottom_part.select_set(True)
bpy.context.view_layer.objects.active = main_body
bpy.ops.object.join()


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
