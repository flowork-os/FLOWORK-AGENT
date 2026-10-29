# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_sun_hat_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct sun hat in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

hat_color = bpy.data.materials.new(name='Hat Color')
hat_color.diffuse_color = (0.85, 0.65, 0.45, 1)  # Different light brown
ribbon_color = bpy.data.materials.new(name='Ribbon Color')
ribbon_color.diffuse_color = (0.9, 0, 0, 1)  # Bright red

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

brim = add_cylinder(2, 0.1, (0, 0, 0), 'Hat Brim', hat_color)
crown = bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0.6))
bpy.context.object.name = 'Hat Crown'
bpy.context.object.data.materials.append(hat_color)

ribbon = add_cylinder(1.05, 0.1, (0, 0, 0.6), 'Hat Ribbon', ribbon_color)

bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(-0.25, -1.05, 0.6), rotation=(math.pi/2, 0, 0))
left_loop = bpy.context.object
left_loop.name = 'Left Bow Loop'
left_loop.data.materials.append(ribbon_color)

bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(0.25, -1.05, 0.6), rotation=(math.pi/2, 0, 0))
right_loop = bpy.context.object
right_loop.name = 'Right Bow Loop'
right_loop.data.materials.append(ribbon_color)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, -1.05, 0.6))
knot = bpy.context.object
knot.name = 'Bow Knot'
knot.data.materials.append(ribbon_color)


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
