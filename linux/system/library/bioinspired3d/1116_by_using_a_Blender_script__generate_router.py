# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__generate_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, generate router.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model parts
material_body = bpy.data.materials.new(name='Body')
material_body.diffuse_color = (0.1, 0.1, 0.1, 1)
material_antenna = bpy.data.materials.new(name='Antenna')
material_antenna.diffuse_color = (0.1, 0.1, 0.1, 1)
material_light = bpy.data.materials.new(name='Light')
material_light.diffuse_color = (0, 1, 0, 1)

# Create the router body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
router_body = bpy.context.object
router_body.scale = (2, 1, 0.2)
router_body.name = 'Router'
router_body.data.materials.append(material_body)

# Function to add an antenna

def add_antenna(x_offset):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_offset, 0, 1.2))
    antenna = bpy.context.object
    antenna.name = 'Antenna'
    antenna.data.materials.append(material_antenna)

# Create antennas
for i in range(-1, 2):
    add_antenna(i * 1.5)

# Function to add a light

def add_light(x_offset):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_offset, 1.1, 0.6))
    light = bpy.context.object
    light.name = 'Light'
    light.data.materials.append(material_light)

# Create lights
for i in range(-1, 2):
    add_light(i * 0.5)


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
