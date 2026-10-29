# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_that_makes_a_model_of_basketball" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code that makes a model of basketball.

import bpy

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the basketball
orange_material = bpy.data.materials.new(name='OrangeMaterial')
orange_material.diffuse_color = (1.0, 0.55, 0.0, 1)
black_material = bpy.data.materials.new(name='BlackMaterial')
black_material.diffuse_color = (0, 0, 0, 1)

# Function to create a cylinder line
def create_cylinder(radius, depth, location, rotation, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    line = bpy.context.object
    line.name = name
    line.data.materials.append(material)

# Create the basketball
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
basketball_object = bpy.context.object
basketball_object.name = 'Basketball'
basketball_object.data.materials.append(orange_material)

# Create the lines
create_cylinder(1.01, 0.05, (0, 0, 0), (1.5708, 0, 0), 'Horizontal Line', black_material)
create_cylinder(1.01, 0.05, (0, 0, 0), (0, 1.5708, 0), 'Vertical Line', black_material)
create_cylinder(1.01, 0.05, (0, 0, 0), (0.7854, 0, 0), 'Diagonal Line 1', black_material)
create_cylinder(1.01, 0.05, (0, 0, 0), (-0.7854, 0, 0), 'Diagonal Line 2', black_material)


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
