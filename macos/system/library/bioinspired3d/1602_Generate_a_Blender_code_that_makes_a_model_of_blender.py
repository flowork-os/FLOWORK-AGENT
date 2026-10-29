# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_makes_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that makes a model of blender

import bpy

# Clear all existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with specific colors
mat_base = bpy.data.materials.new(name="Base Material")
mat_base.diffuse_color = (0.2, 0.2, 0.2, 1)
mat_button = bpy.data.materials.new(name="Button Material")
mat_button.diffuse_color = (0.8, 0.1, 0.1, 1)
mat_jar = bpy.data.materials.new(name="Jar Material")
mat_jar.diffuse_color = (0.8, 0.8, 0.8, 0.3)
mat_lid = bpy.data.materials.new(name="Lid Material")
mat_lid.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base
base_object = create_cylinder(1, 0.5, (0, 0, 0.25), "Base", mat_base)

# Create buttons using a loop
for index in range(3):
    create_cylinder(0.1, 0.2, (0.4 * (index - 1), 0.9, 0.1), f"Button_{index + 1}", mat_button)

# Create the jar
jar_object = create_cylinder(0.8, 1.5, (0, 0, 1.25), "Jar", mat_jar)

# Create the lid
lid_object = create_cylinder(0.85, 0.1, (0, 0, 2), "Lid", mat_lid)


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
