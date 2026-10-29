# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_to_create_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script to create a model of bird feeder.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class WoodStructure:
    def __init__(self):
        self.material = bpy.data.materials.new(name='WoodMaterial')
        self.material.diffuse_color = (0.55, 0.27, 0.07, 1)

    def add_cylinder(self, radius, height, position, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(self.material)

    def create_structure(self):
        self.add_cylinder(0.5, 0.1, (0, 0, 0), 'Base')
        self.add_cylinder(0.05, 1, (0, 0, 0.55), 'Stand')
        self.add_cylinder(0.4, 0.1, (0, 0, 1.1), 'Feeder Tray')
        bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=0.3, location=(0, 0, 1.35))
        roof = bpy.context.object
        roof.name = 'Roof'
        roof.data.materials.append(self.material)

# Instantiate and create the wood structure
wood_structure = WoodStructure()
wood_structure.create_structure()


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
