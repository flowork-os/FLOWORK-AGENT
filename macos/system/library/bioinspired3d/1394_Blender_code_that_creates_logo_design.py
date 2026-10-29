# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_creates_logo_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that creates logo design

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a sphere representing the globe

def create_globe():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    globe_object = bpy.context.object
    globe_object.name = 'Planet'
    globe_material = bpy.data.materials.new(name='PlanetMaterial')
    globe_material.diffuse_color = (0.2, 0.5, 0.8, 1)
    globe_object.data.materials.append(globe_material)
    return globe_object

# Create the globe
create_globe()

# Create orbiting rings around the globe
for index in range(3):
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), major_radius=1.3, minor_radius=0.02, rotation=(index * 1.0472, 0, 0))
    ring = bpy.context.object
    ring.name = f'OrbitRing_{index + 1}'
    ring_material = bpy.data.materials.new(name=f'RingMaterial_{index + 1}')
    ring_material.diffuse_color = (0.8, 0.2, 0.2, 1)
    ring.data.materials.append(ring_material)


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
