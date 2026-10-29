# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_to_make_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script to make drum

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the drum
mat_body = bpy.data.materials.new(name='DrumBodyMaterial')
mat_body.diffuse_color = (0.5, 0.25, 0.1, 1)
mat_top = bpy.data.materials.new(name='DrumTopMaterial')
mat_top.diffuse_color = (0.8, 0.8, 0.8, 1)

# Class to handle drum creation
class Drum:
    def __init__(self, radius, depth, location, name, material):
        self.radius = radius
        self.depth = depth
        self.location = location
        self.name = name
        self.material = material
        self.create()

    def create(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=self.depth, location=self.location)
        obj = bpy.context.object
        obj.name = self.name
        obj.data.materials.append(self.material)

# Create drum components
Drum(1, 0.5, (0, 0, 0), 'Drum Body', mat_body)
Drum(1.05, 0.1, (0, 0, 0.3), 'Drum Top', mat_top)
Drum(1.05, 0.1, (0, 0, -0.3), 'Drum Bottom', mat_body)


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
