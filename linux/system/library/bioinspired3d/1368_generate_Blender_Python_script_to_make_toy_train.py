# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_to_make_toy_train" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script to make toy train.

import bpy
import math

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the train components
locomotive_color = bpy.data.materials.new(name="Locomotive Color")
locomotive_color.diffuse_color = (0.8, 0.1, 0.1, 1)  # Vivid red
wheel_color = bpy.data.materials.new(name="Wheel Color")
wheel_color.diffuse_color = (0.1, 0.1, 0.1, 1)  # Jet black
track_color = bpy.data.materials.new(name="Track Color")
track_color.diffuse_color = (0.5, 0.5, 0.5, 1)  # Concrete gray

# Define a class for the Train
class Train:
    def __init__(self):
        self.create_locomotive()
        self.create_carriages()
        self.create_track()

    def create_locomotive(self):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
        body = bpy.context.object
        body.name = "Locomotive Body"
        body.data.materials.append(locomotive_color)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0.4, 1))
        chimney = bpy.context.object
        chimney.name = "Chimney"
        chimney.data.materials.append(locomotive_color)

        for i in range(4):
            wheel_x = -0.3 + 0.2 * (i % 2)
            wheel_y = -0.5 + i // 2
            self.create_wheel(wheel_x, wheel_y, i + 1)

    def create_wheel(self, x, y, index):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.1, location=(x, y, 0.1), rotation=(math.pi/2, 0, 0))
        wheel = bpy.context.object
        wheel.name = f"Wheel {index}"
        wheel.data.materials.append(wheel_color)

    def create_carriages(self):
        for j in range(3):
            bpy.ops.mesh.primitive_cube_add(size=0.8, location=(1.2 + j, 0, 0.4))
            carriage = bpy.context.object
            carriage.name = f"Carriage {j + 1}"
            carriage.data.materials.append(locomotive_color)

            for i in range(4):
                wheel_x = 1.2 + j - 0.3 + 0.2 * (i % 2)
                wheel_y = -0.5 + i // 2
                self.create_wheel(wheel_x, wheel_y, j * 4 + i + 5)

    def create_track(self):
        bpy.ops.mesh.primitive_torus_add(major_radius=5, minor_radius=0.1, location=(0, 0, 0))
        track = bpy.context.object
        track.name = "Track"
        track.data.materials.append(track_color)

# Instantiate the Train
Train()


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
