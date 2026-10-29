# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_sofa_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of sofa using blender script

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the sofa's material
material_for_sofa = bpy.data.materials.new(name="Sofa Material")
material_for_sofa.diffuse_color = (0.5, 0.1, 0.1, 1)  # Dark red shade

# Use a class to manage sofa creation
class Sofa:
    def __init__(self):
        self.material = material_for_sofa

    def create_part(self, name, location, scale):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        part = bpy.context.object
        part.name = name
        part.scale = scale
        part.data.materials.append(self.material)

# Instantiate the Sofa class
sofa = Sofa()

# Create the sofa components
sofa.create_part("Sofa Base", (0, 0, 0.5), (2, 1, 0.5))
sofa.create_part("Sofa Backrest", (0, -1, 1.25), (2, 0.1, 1))

# Add armrests
for idx in range(2):
    armrest_position = 1.9 * (idx * 2 - 1)
    sofa.create_part(f"Sofa Armrest {idx + 1}", (armrest_position, 0, 1), (0.1, 1, 0.5))


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
