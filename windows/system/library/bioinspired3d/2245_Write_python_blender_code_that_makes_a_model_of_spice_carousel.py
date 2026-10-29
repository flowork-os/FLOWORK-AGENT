# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_python_blender_code_that_makes_a_model_of_spice_carousel" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write python blender code that makes a model of spice carousel.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

carousel_color_material = bpy.data.materials.new(name='Carousel Color Material')
carousel_color_material.diffuse_color = (0.4, 0.4, 0.4, 1)
jar_color_material = bpy.data.materials.new(name='Jar Color Material')
jar_color_material.diffuse_color = (1, 1, 1, 1)
lid_color_material = bpy.data.materials.new(name='Lid Color Material')
lid_color_material.diffuse_color = (0.15, 0.15, 0.15, 1)

def create_spice_jar(index, x, y):
    create_cylinder(0.2, 0.6, (x, y, 0.4), f'Jar {index + 1}', jar_color_material)
    create_cylinder(0.22, 0.1, (x, y, 0.75), f'Lid {index + 1}', lid_color_material)
    create_cylinder(0.18, 0.05, (x, y, 0.8), f'Shaker Top {index + 1}', lid_color_material)

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

create_cylinder(2, 0.2, (0, 0, 0), 'Base', carousel_color_material)
create_cylinder(0.1, 2, (0, 0, 1.1), 'Handle', carousel_color_material)

for i in range(12):
    angle_rad = i * (2 * math.pi / 12)
    x_coord = 1.5 * math.cos(angle_rad)
    y_coord = 1.5 * math.sin(angle_rad)
    create_spice_jar(i, x_coord, y_coord)


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
