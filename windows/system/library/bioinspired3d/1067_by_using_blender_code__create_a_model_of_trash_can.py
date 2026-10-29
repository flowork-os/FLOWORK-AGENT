# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code__create_a_model_of_trash_can" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code, create a model of trash can

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the trash can
material_trash = bpy.data.materials.new(name='Material_Trash')
material_trash.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_trash)
    return obj

# Create the body of the trash can
trash_body = create_cylinder(1, 2, (0, 0, 1), 'Trash Can Body')
# Create the lid of the trash can
trash_lid = create_cylinder(1.05, 0.1, (0, 0, 2.05), 'Trash Can Lid')


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
