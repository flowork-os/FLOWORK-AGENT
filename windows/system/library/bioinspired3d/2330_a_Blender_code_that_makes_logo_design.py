# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_makes_logo_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that makes logo design

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main globe object
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
planet = bpy.context.object
planet.name = 'Globe'

# Assign a blue material to the globe
material_blue = bpy.data.materials.new(name='BlueGlobeMaterial')
material_blue.diffuse_color = (0.2, 0.5, 0.8, 1)
planet.data.materials.append(material_blue)

# Generate the orbit lines
orbits_collection = []
for j in range(3):
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), major_radius=1.3, minor_radius=0.02, rotation=(j * 1.0472, 0, 0))
    orbit_line = bpy.context.object
    orbit_line.name = f'Orbit_{j + 1}'
    orbits_collection.append(orbit_line)
    # Create a red material for each orbit line
    material_red = bpy.data.materials.new(name=f'RedOrbitMaterial_{j + 1}')
    material_red.diffuse_color = (0.8, 0.2, 0.2, 1)
    orbit_line.data.materials.append(material_red)


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
