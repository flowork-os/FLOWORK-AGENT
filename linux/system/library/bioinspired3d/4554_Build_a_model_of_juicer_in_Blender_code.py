# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_juicer_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of juicer in Blender code

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with defined colors
material_base = bpy.data.materials.new(name="Material Base")
material_base.diffuse_color = (0.2, 0.2, 0.2, 1)
material_container = bpy.data.materials.new(name="Material Container")
material_container.diffuse_color = (0.8, 0.8, 0.8, 1)
material_spout = bpy.data.materials.new(name="Material Spout")
material_spout.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the main components using the helper function
base_cylinder = create_cylinder(1, 0.5, (0, 0, 0.25), "Base", material_base)
container_cylinder = create_cylinder(0.9, 1.2, (0, 0, 1.1), "Juice Container", material_container)
feeding_tube_cylinder = create_cylinder(0.2, 0.8, (0, 0, 1.7), "Feeding Tube", material_container)
spout_cylinder = create_cylinder(0.1, 0.4, (0.9, 0, 0.9), "Spout", material_spout)

# Create pulp container
pulp_container_cylinder = create_cylinder(0.5, 0.6, (-1.2, 0, 0.3), "Pulp Container", material_container)


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
