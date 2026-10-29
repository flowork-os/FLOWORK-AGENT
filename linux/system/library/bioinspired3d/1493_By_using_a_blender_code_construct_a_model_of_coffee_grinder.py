# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code_construct_a_model_of_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code construct a model of coffee grinder.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name='Metallic')
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
wood_material = bpy.data.materials.new(name='Wooden')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Construct the components of the model
base_cylinder = create_cylinder(1, 0.2, (0, 0, 0), 'Base', wood_material)
body_cylinder = create_cylinder(0.8, 1.5, (0, 0, 0.85), 'Body', metal_material)
top_cylinder = create_cylinder(0.9, 0.1, (0, 0, 1.55), 'Top', metal_material)

# Create the handle using a cylinder
handle_cylinder = create_cylinder(0.05, 1, (0.9, 0, 1.65), 'Handle', metal_material)
handle_cylinder.rotation_euler = (0, math.pi/2, 0)

# Create the knob using a UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(1.45, 0, 1.65))
knob_sphere = bpy.context.object
knob_sphere.name = 'Knob'
knob_sphere.data.materials.append(wood_material)


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
