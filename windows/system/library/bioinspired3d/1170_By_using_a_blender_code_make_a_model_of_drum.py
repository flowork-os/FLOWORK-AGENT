# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code_make_a_model_of_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code make a model of drum

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material colors for the drum
mat_drum_body = bpy.data.materials.new(name="Drum Body")
mat_drum_body.diffuse_color = (0.7, 0.1, 0.1, 1)
mat_drum_head = bpy.data.materials.new(name="Drum Head")
mat_drum_head.diffuse_color = (0.9, 0.9, 0.9, 1)
mat_drum_stick = bpy.data.materials.new(name="Drum Stick")
mat_drum_stick.diffuse_color = (0.5, 0.3, 0.1, 1)

# Create drum components using a class
class Drum:
    def __init__(self):
        self.create_body()
        self.create_head()
        self.create_sticks()
        self.add_patterns()

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
        body = bpy.context.object
        body.name = "Drum Body"
        body.data.materials.append(mat_drum_body)

    def create_head(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.05, location=(0, 0, 1.525))
        head = bpy.context.object
        head.name = "Drum Head"
        head.data.materials.append(mat_drum_head)

    def create_sticks(self):
        for i in range(2):
            x_pos = 1.5 * (i * 2 - 1)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_pos, 0, 0.5))
            stick = bpy.context.object
            stick.name = f"Drumstick {i + 1}"
            stick.data.materials.append(mat_drum_stick)

    def add_patterns(self):
        for z in [0.3, 1.2]:
            bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.05, location=(0, 0, z))
            pattern = bpy.context.object
            pattern.name = "Pattern"
            pattern.data.materials.append(mat_drum_head)

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
