# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_teapot_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate teapot using blender python code

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the teapot
teapot_material = bpy.data.materials.new(name="Teapot Material")
teapot_material.diffuse_color = (0.8, 0.5, 0.3, 1)  # Brownish color

# Function to create a mesh object
def create_mesh(primitive, **kwargs):
    bpy.ops.mesh.primitive_uv_sphere_add(**kwargs) if primitive == 'sphere' else bpy.ops.mesh.primitive_cylinder_add(**kwargs) if primitive == 'cylinder' else bpy.ops.mesh.primitive_torus_add(**kwargs)
    obj = bpy.context.object
    obj.data.materials.append(teapot_material)
    return obj

# Create teapot components
body = create_mesh('sphere', radius=1, location=(0, 0, 0))
body.name = "Teapot Body"

spout = create_mesh('cylinder', radius=0.1, depth=1, location=(1, 0, 0))
spout.name = "Teapot Spout"
spout.rotation_euler = (0, math.pi / 6, 0)
spout.location = (0.8, 0, 0.4)

handle = create_mesh('torus', major_radius=0.6, minor_radius=0.1, location=(-1, 0, 0))
handle.name = "Teapot Handle"
handle.rotation_euler = (math.pi / 2, 0, 0)
handle.location = (-0.8, 0, 0.4)

lid = create_mesh('sphere', radius=0.5, location=(0, 0, 1))
lid.name = "Teapot Lid"
lid.scale[2] = 0.5

knob = create_mesh('sphere', radius=0.1, location=(0, 0, 1.3))
knob.name = "Teapot Knob"


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
