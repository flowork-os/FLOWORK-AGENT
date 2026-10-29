# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_make_cat_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to make cat bed.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bed
light_gray_material = bpy.data.materials.new(name='Light Gray')
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)
dark_brown_material = bpy.data.materials.new(name='Dark Brown')
dark_brown_material.diffuse_color = (0.4, 0.2, 0.1, 1)

# Function to create a cylinder

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base of the cat bed
base_object = add_cylinder(1, 0.2, (0, 0, 0), 'Base', light_gray_material)

# Create the raised sides using a torus
bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.2, location=(0, 0, 0.2))
sides_object = bpy.context.object
sides_object.name = 'Sides'
sides_object.data.materials.append(dark_brown_material)

# Create the soft interior layer
soft_interior_object = add_cylinder(0.9, 0.15, (0, 0, 0.025), 'Soft Interior', light_gray_material)


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
