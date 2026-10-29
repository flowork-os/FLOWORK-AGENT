# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code_construct_a_model_of_toy_train" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code construct a model of toy train

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the train components
body_material = bpy.data.materials.new(name="Body Material")
body_material.diffuse_color = (0.8, 0.1, 0.1, 1)  # Bright red
wheel_material = bpy.data.materials.new(name="Wheel Material")
wheel_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Dark gray
track_material = bpy.data.materials.new(name="Track Material")
track_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Neutral gray

# Function to create a wheel

def create_wheel(x_pos, y_pos, wheel_index):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.1, location=(x_pos, y_pos, 0.1), rotation=(math.pi/2, 0, 0))
    wheel = bpy.context.object
    wheel.name = f"Wheel {wheel_index}"
    wheel.data.materials.append(wheel_material)

# Create the locomotive
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
locomotive = bpy.context.object
locomotive.name = "Locomotive"
locomotive.data.materials.append(body_material)

# Add chimney to the locomotive
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0.4, 1))
chimney = bpy.context.object
chimney.name = "Chimney"
chimney.data.materials.append(body_material)

# Adding wheels to the locomotive
for i in range(4):
    wheel_x = -0.3 + 0.2 * (i % 2)
    wheel_y = -0.5 + i // 2
    create_wheel(wheel_x, wheel_y, i + 1)

# Create carriages
for j in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.8, location=(1.2 + j, 0, 0.4))
    carriage = bpy.context.object
    carriage.name = f"Carriage {j + 1}"
    carriage.data.materials.append(body_material)

    # Adding wheels to each carriage
    for i in range(4):
        carriage_wheel_x = 1.2 + j - 0.3 + 0.2 * (i % 2)
        carriage_wheel_y = -0.5 + i // 2
        create_wheel(carriage_wheel_x, carriage_wheel_y, j * 4 + i + 5)

# Create the track
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
