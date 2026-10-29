# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_create_a_model_of_light_bulb" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to create a model of light bulb

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the lamp components
white_bulb = bpy.data.materials.new(name="White Bulb")
white_bulb.diffuse_color = (1, 1, 1, 1)  # Pure white
charcoal_base = bpy.data.materials.new(name="Charcoal Base")
charcoal_base.diffuse_color = (0.2, 0.2, 0.2, 1)  # Charcoal gray

# Create bulb mesh
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 1))
bulb_object = bpy.context.object
bulb_object.name = "Lamp Bulb"
bulb_object.data.materials.append(white_bulb)

# Create base mesh
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.6, location=(0, 0, 0.3))
base_object = bpy.context.object
base_object.name = "Lamp Base"
base_object.data.materials.append(charcoal_base)

# Create ridges around the base
for index in range(1, 5):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.02, location=(0, 0, 0.3 + (index * 0.1)))
    ridge = bpy.context.object
    ridge.name = f"Ridge {index}"
    ridge.data.materials.append(charcoal_base)


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
