# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_generating_a_model_of_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for generating a model of router

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
mat_black = bpy.data.materials.new(name="Black Material")
mat_black.diffuse_color = (0.0, 0.0, 0.0, 1)
mat_green = bpy.data.materials.new(name="Green Material")
mat_green.diffuse_color = (0.0, 1.0, 0.0, 1)

# Add the router body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
router_body = bpy.context.object
router_body.name = "RouterCore"
router_body.scale[0] = 1.5
router_body.scale[2] = 0.2
router_body.data.materials.append(mat_black)

# Create antennae using a loop
for index in range(2):
    x_coord = 0.7 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_coord, -0.5, 1))
    antenna = bpy.context.object
    antenna.name = f"Antenna_{index + 1}"
    antenna.data.materials.append(mat_black)

# Generate LED indicators
for index in range(5):
    x_position = -0.6 + index * 0.3
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_position, 1.1, 0.6))
    led_light = bpy.context.object
    led_light.name = f"LED_{index + 1}"
    led_light.data.materials.append(mat_green)


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
