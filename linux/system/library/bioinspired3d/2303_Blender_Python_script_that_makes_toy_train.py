# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_makes_toy_train" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that makes toy train.

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the train
train_material = bpy.data.materials.new(name="Train Material")
train_material.diffuse_color = (0.8, 0.1, 0.1, 1)  # Bright red
wheel_material = bpy.data.materials.new(name="Wheel Material")
wheel_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Deep black
track_material = bpy.data.materials.new(name="Track Material")
track_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Light gray

# Generate the locomotive
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
locomotive = bpy.context.object
locomotive.name = "Locomotive"
locomotive.data.materials.append(train_material)

# Add chimney to locomotive
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0.4, 1))
chimney = bpy.context.object
chimney.name = "Chimney"
chimney.data.materials.append(train_material)

# Create wheels for locomotive
for i in range(4):
    wheel_x = -0.3 + 0.2 * (i % 2)
    wheel_y = -0.5 + i // 2
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.1, location=(wheel_x, wheel_y, 0.1), rotation=(math.pi/2, 0, 0))
    wheel = bpy.context.object
    wheel.name = f"Locomotive Wheel {i + 1}"
    wheel.data.materials.append(wheel_material)

# Create carriages
for j in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.8, location=(1.2 + j, 0, 0.4))
    carriage = bpy.context.object
    carriage.name = f"Carriage {j + 1}"
    carriage.data.materials.append(train_material)

    # Add wheels to each carriage
    for i in range(4):
        wheel_x = 1.2 + j - 0.3 + 0.2 * (i % 2)
        wheel_y = -0.5 + i // 2
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.1, location=(wheel_x, wheel_y, 0.1), rotation=(math.pi/2, 0, 0))
        wheel = bpy.context.object
        wheel.name = f"Carriage Wheel {j * 4 + i + 1}"
        wheel.data.materials.append(wheel_material)

# Create circular track
bpy.ops.mesh.primitive_torus_add(major_radius=5, minor_radius=0.1, location=(0, 0, 0))
track = bpy.context.object
track.name = "Track"
track.data.materials.append(track_material)


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
