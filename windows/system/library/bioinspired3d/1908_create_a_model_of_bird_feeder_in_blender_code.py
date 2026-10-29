# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_bird_feeder_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of bird feeder in blender code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize wood material
wood_mat = bpy.data.materials.new(name="WoodTexture")
wood_mat.diffuse_color = (0.55, 0.27, 0.07, 1)

class Structure:
    def __init__(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        self.obj = bpy.context.object
        self.obj.name = name
        self.obj.data.materials.append(wood_mat)

class Roof:
    def __init__(self, radius1, radius2, depth, location, name):
        bpy.ops.mesh.primitive_cone_add(radius1=radius1, radius2=radius2, depth=depth, location=location)
        self.obj = bpy.context.object
        self.obj.name = name
        self.obj.data.materials.append(wood_mat)

# Create main body and roof
main_body = Structure(0.5, 1.0, (0, 0, 0.5), "MainBody")
roof = Roof(0.5, 0.1, 0.5, (0, 0, 1.25), "Roof")

# Create perch
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=(0, 0.55, 0.5), rotation=(1.57, 0, 0))
perch = bpy.context.object
perch.name = "Perch"
perch.data.materials.append(wood_mat)


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
