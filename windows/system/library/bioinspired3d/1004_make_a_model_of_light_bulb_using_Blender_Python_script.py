# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_light_bulb_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of light bulb using Blender Python script

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a material

def create_material(name, color):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    return material

# Create the bulb using a UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1.5))
bulb_object = bpy.context.object
bulb_object.name = 'LightBulb'
bulb_object.data.materials.append(create_material('LightBulbMaterial', (1, 1, 1, 1)))

# Create the base using a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 0.5))
base_object = bpy.context.object
base_object.name = 'LampBase'
base_object.data.materials.append(create_material('BaseMaterial', (0.5, 0.5, 0.5, 1)))


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
