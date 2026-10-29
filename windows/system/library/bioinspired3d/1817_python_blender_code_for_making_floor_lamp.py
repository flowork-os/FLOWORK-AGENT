# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_making_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for making floor lamp.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
metallic_surface = bpy.data.materials.new(name="Metallic Surface")
metallic_surface.diffuse_color = (0.5, 0.5, 0.5, 1)
white_surface = bpy.data.materials.new(name="White Surface")
white_surface.diffuse_color = (1, 1, 1, 1)

# Creating objects using a class
class Lamp:
    def __init__(self):
        self.create_stand()
        self.create_base()
        self.create_shade()
        self.create_drum()
        self.create_foot_switch()

    def create_stand(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, 1))
        stand = bpy.context.object
        stand.name = "Lamp Stand"
        stand.data.materials.append(metallic_surface)

    def create_base(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0.05))
        base = bpy.context.object
        base.name = "Lamp Base"
        base.data.materials.append(metallic_surface)

    def create_shade(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.8, location=(0, 0, 2.4))
        shade = bpy.context.object
        shade.name = "Lamp Shade"
        shade.data.materials.append(white_surface)

    def create_drum(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.2, location=(0, 0, 2.7))
        drum = bpy.context.object
        drum.name = "Lamp Drum"
        drum.data.materials.append(metallic_surface)

    def create_foot_switch(self):
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.5, 0, 0.05))
        foot_switch = bpy.context.object
        foot_switch.name = "Lamp Foot Switch"
        foot_switch.data.materials.append(metallic_surface)

# Instantiate the Lamp class
Lamp()


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
