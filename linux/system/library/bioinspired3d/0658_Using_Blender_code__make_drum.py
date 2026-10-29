# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code__make_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code, make drum.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum components
body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.5, 0.25, 0.1, 1)  # Rich brown color
head_material = bpy.data.materials.new(name='Head Material')
head_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Soft gray color

# Function to create a cylinder with a specific name and material

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the drum body, top, and bottom
create_cylinder(1, 0.5, (0, 0, 0), 'Drum Body', body_material)
create_cylinder(1.05, 0.1, (0, 0, 0.3), 'Drum Top', head_material)
create_cylinder(1.05, 0.1, (0, 0, -0.3), 'Drum Bottom', body_material)


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
