# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_to_make_a_model_of_fuse" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script to make a model of fuse.

import bpy

# Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
transparent_material = bpy.data.materials.new(name='Transparent Material')
transparent_material.diffuse_color = (0.8, 0.8, 0.8, 1)
metallic_material = bpy.data.materials.new(name='Metallic Material')
metallic_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the Glass Body
create_cylinder(0.1, 1.0, (0, 0, 0), 'Glass Body', transparent_material)

# Create the Metal Caps
create_cylinder(0.12, 0.2, (0, 0, -0.6), 'Metal Cap 1', metallic_material)
create_cylinder(0.12, 0.2, (0, 0, 0.6), 'Metal Cap 2', metallic_material)


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
