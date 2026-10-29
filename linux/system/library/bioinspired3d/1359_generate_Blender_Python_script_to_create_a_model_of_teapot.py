# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_to_create_a_model_of_teapot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script to create a model of teapot

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up the material for the teapot
material_teapot = bpy.data.materials.new(name='Teapot Color')
material_teapot.diffuse_color = (0.8, 0.5, 0.3, 1)  # A warm brown hue

# Create the main body of the teapot
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
body_part = bpy.context.object
body_part.name = 'Teapot Body'
body_part.data.materials.append(material_teapot)

# Adding the spout
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1, location=(1, 0, 0))
spout_part = bpy.context.object
spout_part.name = 'Teapot Spout'
spout_part.rotation_euler = (0, math.pi / 6, 0)
spout_part.location = (0.8, 0, 0.4)
spout_part.data.materials.append(material_teapot)

# Adding the handle
bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.1, location=(-1, 0, 0))
handle_part = bpy.context.object
handle_part.name = 'Teapot Handle'
handle_part.rotation_euler = (math.pi / 2, 0, 0)
handle_part.location = (-0.8, 0, 0.4)
handle_part.data.materials.append(material_teapot)

# Create the lid
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 1))
lid_part = bpy.context.object
lid_part.name = 'Teapot Lid'
lid_part.scale[2] = 0.5
lid_part.data.materials.append(material_teapot)

# Create the knob for the lid
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 1.3))
knob_part = bpy.context.object
knob_part.name = 'Teapot Knob'
knob_part.data.materials.append(material_teapot)


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
