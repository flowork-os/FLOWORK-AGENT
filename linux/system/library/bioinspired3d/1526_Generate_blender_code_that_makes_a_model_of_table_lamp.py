# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_makes_a_model_of_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that makes a model of table lamp.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the lamp components
base_material = bpy.data.materials.new(name='Base Material')
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)
shade_material = bpy.data.materials.new(name='Shade Material')
shade_material.diffuse_color = (1, 1, 1, 0.8)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Function to create a cone
def create_cone(radius1, radius2, depth, location, name, material):
    bpy.ops.mesh.primitive_cone_add(radius1=radius1, radius2=radius2, depth=depth, location=location)
    cone = bpy.context.object
    cone.name = name
    cone.data.materials.append(material)
    return cone

# Create the lamp components
lamp_base = create_cylinder(0.5, 0.1, (0, 0, 0), 'Lamp Base', base_material)
lamp_pole = create_cylinder(0.05, 1, (0, 0, 0.55), 'Lamp Pole', base_material)
lamp_shade = create_cone(0.6, 0.2, 0.8, (0, 0, 1.4), 'Lamp Shade', shade_material)


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
