# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script_make_water_bottle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script make water bottle.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bottle and cap
bottle_material = bpy.data.materials.new(name='BottleMaterial')
bottle_material.diffuse_color = (0.3, 0.6, 0.9, 1)  # A soft blue tone
cap_material = bpy.data.materials.new(name='CapMaterial')
cap_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # A muted gray

# Function to create a cylinder

def add_cylinder(radius, depth, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the bottle body, neck, and cap
bottle_body = add_cylinder(0.3, 1.5, (0, 0, 0.75), 'BottleBody', bottle_material)
bottle_neck = add_cylinder(0.2, 0.3, (0, 0, 1.65), 'BottleNeck', bottle_material)
cap = add_cylinder(0.22, 0.2, (0, 0, 1.85), 'Cap', cap_material)


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
