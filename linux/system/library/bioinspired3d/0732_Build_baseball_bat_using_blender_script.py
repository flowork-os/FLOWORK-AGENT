# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_baseball_bat_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build baseball bat using blender script

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material with a wood-like color
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.4, 0.2, 0.1, 1)

# Create Bat Class
class Bat:
    def __init__(self, radius_body, depth_body, radius_handle, depth_handle, knob_radius):
        self.body = self.create_body(radius_body, depth_body)
        self.handle = self.create_handle(radius_handle, depth_handle)
        self.knob = self.create_knob(knob_radius)

    def create_body(self, radius, depth):
        return self.add_cylinder(radius, depth, (0, 0, 0.6), 'Bat Body')

    def create_handle(self, radius, depth):
        return self.add_cylinder(radius, depth, (0, 0, -0.15), 'Handle Grip')

    def create_knob(self, radius):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0, 0, -0.3))
        knob = bpy.context.object
        knob.name = 'Handle Knob'
        knob.data.materials.append(wood_material)
        return knob

    def add_cylinder(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(wood_material)
        return obj

# Instantiate Bat
bat = Bat(0.05, 1.2, 0.03, 0.3, 0.04)


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
