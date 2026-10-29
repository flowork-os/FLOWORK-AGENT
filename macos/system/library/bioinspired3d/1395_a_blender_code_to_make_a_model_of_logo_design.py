# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_make_a_model_of_logo_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to make a model of logo design

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to handle the creation of the globe and its orbits
class GlobeModel:
    def __init__(self):
        self.create_globe()
        self.create_orbits()

    def create_globe(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
        globe_instance = bpy.context.object
        globe_instance.name = 'Earth'
        material = bpy.data.materials.new(name='EarthMaterial')
        material.diffuse_color = (0.2, 0.5, 0.8, 1)
        globe_instance.data.materials.append(material)

    def create_orbits(self):
        for idx in range(3):
            bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), major_radius=1.3, minor_radius=0.02, rotation=(idx * 1.0472, 0, 0))
            orbit_instance = bpy.context.object
            orbit_instance.name = f'OrbitLayer_{idx + 1}'
            orbit_material = bpy.data.materials.new(name=f'OrbitMaterial_{idx + 1}')
            orbit_material.diffuse_color = (0.8, 0.2, 0.2, 1)
            orbit_instance.data.materials.append(orbit_material)

# Instantiate the globe model
GlobeModel()


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
