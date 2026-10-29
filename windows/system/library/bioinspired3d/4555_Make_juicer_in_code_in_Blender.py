# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_juicer_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make juicer in code in Blender

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)
container_material = bpy.data.materials.new(name="Container Material")
container_material.diffuse_color = (0.8, 0.8, 0.8, 1)
spout_material = bpy.data.materials.new(name="Spout Material")
spout_material.diffuse_color = (0.5, 0.5, 0.5, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base = bpy.context.object
base.name = "Base"
base.data.materials.append(base_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.2, location=(0, 0, 1.1))
container = bpy.context.object
container.name = "Juice Container"
container.data.materials.append(container_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.8, location=(0, 0, 1.7))
feeding_tube = bpy.context.object
feeding_tube.name = "Feeding Tube"
feeding_tube.data.materials.append(container_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(0.9, 0, 0.9), rotation=(0, math.pi / 2, 0))
spout = bpy.context.object
spout.name = "Spout"
spout.data.materials.append(spout_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.6, location=(-1.2, 0, 0.3))
pulp_container = bpy.context.object
pulp_container.name = "Pulp Container"
pulp_container.data.materials.append(container_material)


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
