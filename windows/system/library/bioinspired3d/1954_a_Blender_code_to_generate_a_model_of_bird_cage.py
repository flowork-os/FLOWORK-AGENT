# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_to_generate_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code to generate a model of bird cage

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_surface = bpy.data.materials.new(name="MetalSurface")
metal_surface.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray

class ObjectCreator:
    @staticmethod
    def add_cylinder(radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(metal_surface)
        return obj

base_object = ObjectCreator.add_cylinder(1, 0.1, (0, 0, 0), "Base")

for i in range(16):
    angle = (2 * math.pi / 16) * i
    x_coord = math.cos(angle)
    y_coord = math.sin(angle)
    ObjectCreator.add_cylinder(0.05, 2, (x_coord, y_coord, 1), f"VerticalBar_{i + 1}")

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome_object = bpy.context.object

dome_object.name = "Dome"
dome_object.scale[2] = 0.5  # Flattening the sphere

dome_object.data.materials.append(metal_surface)

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door_object = bpy.context.object

door_object.name = "MainDoor"
door_object.scale[2] = 1.5  # Increase height

door_object.rotation_euler[2] = math.pi / 2  # Rotate to vertical

door_object.location[0] = 1.05  # Position adjustment

door_object.location[2] = 1  # Centering vertically


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
