# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_to_make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script to make a model of blender

import bpy

# Remove all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
base_mat = bpy.data.materials.new(name="Main Material")
base_mat.diffuse_color = (0.4, 0.4, 0.4, 1)  # Light gray

translucent_mat = bpy.data.materials.new(name="Translucent Material")
translucent_mat.diffuse_color = (1, 1, 1, 0.15)  # Translucent white

# Create shapes using an object-oriented approach
class Cylinder:
    def __init__(self, radius, depth, location, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        self.object = bpy.context.object
        self.object.name = name
        self.object.data.materials.append(material)

# Instantiate shapes
base_shape = Cylinder(1, 0.2, (0, 0, 0.1), "Base", base_mat)
container_shape = Cylinder(0.9, 3, (0, 0, 1.6), "Container", translucent_mat)
lid_shape = Cylinder(0.95, 0.1, (0, 0, 3.1), "Lid", base_mat)
cap_shape = Cylinder(0.3, 0.2, (0, 0, 3.25), "Cap", base_mat)

# Create measurement markings
for i in range(1, 11):
    bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.85, 0, 0.2 * i))
    marking_obj = bpy.context.object
    marking_obj.name = f"Measurement {i}"
    marking_obj.data.materials.append(base_mat)


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
