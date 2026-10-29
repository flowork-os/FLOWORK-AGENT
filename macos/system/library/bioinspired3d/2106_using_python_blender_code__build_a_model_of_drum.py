# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code__build_a_model_of_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code, build a model of drum.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum components
body_material = bpy.data.materials.new(name="Body Material")
body_material.diffuse_color = (0.8, 0.1, 0.1, 1)
head_material = bpy.data.materials.new(name="Head Material")
head_material.diffuse_color = (0.95, 0.95, 0.95, 1)
stick_material = bpy.data.materials.new(name="Stick Material")
stick_material.diffuse_color = (0.5, 0.25, 0.05, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the drum body
create_cylinder(1, 1.5, (0, 0, 0.75), "Drum Body", body_material)

# Create the drumhead
create_cylinder(1, 0.05, (0, 0, 1.525), "Drumhead", head_material)

# Create drumsticks
for index in range(2):
    position_x = 1.5 * (index * 2 - 1)
    create_cylinder(0.05, 1, (position_x, 0, 0.5), f"Drumstick {index + 1}", stick_material)

# Add decorative patterns
bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.05, location=(0, 0, 0.3))
pattern_top = bpy.context.object
pattern_top.name = "Top Pattern"
pattern_top.data.materials.append(head_material)

bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.05, location=(0, 0, 1.2))
pattern_bottom = bpy.context.object
pattern_bottom.name = "Bottom Pattern"
pattern_bottom.data.materials.append(head_material)


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
