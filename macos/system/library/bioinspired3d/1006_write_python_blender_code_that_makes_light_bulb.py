# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_makes_light_bulb" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that makes light bulb.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials directly
bulb_mat = bpy.data.materials.new('BulbMaterial')
bulb_mat.diffuse_color = (1, 1, 1, 1)
base_mat = bpy.data.materials.new('BaseMaterial')
base_mat.diffuse_color = (0.5, 0.5, 0.5, 1)

# Add a sphere for the bulb
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1.5))
light_bulb = bpy.context.object
light_bulb.name = 'LightBulb'
light_bulb.data.materials.append(bulb_mat)

# Add a cylinder for the base
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 0.5))
lamp_base = bpy.context.object
lamp_base.name = 'LampBase'
lamp_base.data.materials.append(base_mat)


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
