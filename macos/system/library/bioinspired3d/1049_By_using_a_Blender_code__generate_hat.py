# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__generate_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, generate hat

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the hat and band
brown_hat = bpy.data.materials.new(name='Brown Hat')
brown_hat.diffuse_color = (0.5, 0.25, 0.1, 1)

black_band = bpy.data.materials.new(name='Black Band')
black_band.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to add a cylinder

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the brim, crown, and band using the helper function
brim = add_cylinder(2, 0.1, (0, 0, 0), 'Brim', brown_hat)
add_cylinder(1, 2, (0, 0, 1.05), 'Crown', brown_hat)
add_cylinder(1.05, 0.2, (0, 0, 0.9), 'Band', black_band)


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
