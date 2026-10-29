# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code__build_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code, build drum

import bpy
import math

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the drum
material_drum = bpy.data.materials.new(name="Material Drum")
material_drum.diffuse_color = (0.5, 0.25, 0.1, 1)
material_head = bpy.data.materials.new(name="Material Head")
material_head.diffuse_color = (0.8, 0.8, 0.8, 1)
material_rod = bpy.data.materials.new(name="Material Rod")
material_rod.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create the drum components using a method
class Drum:
    def __init__(self):
        self.create_body()
        self.create_head()
        self.create_tension_rods()

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
        drum_body = bpy.context.object
        drum_body.name = "Drum Body"
        drum_body.data.materials.append(material_drum)

    def create_head(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.55))
        drumhead = bpy.context.object
        drumhead.name = "Drumhead"
        drumhead.data.materials.append(material_head)

    def create_tension_rods(self):
        for i in range(8):
            angle = i * (2 * math.pi / 8)
            x_pos = 1.1 * math.cos(angle)
            y_pos = 1.1 * math.sin(angle)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.6, location=(x_pos, y_pos, 0.8))
            rod = bpy.context.object
            rod.name = f"Tension Rod {i + 1}"
            rod.data.materials.append(material_rod)

# Instantiate the drum
Drum()


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
