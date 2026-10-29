# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_builds_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that builds router.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts
mat_body = bpy.data.materials.new(name='Main Body Material')
mat_body.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_antenna = bpy.data.materials.new(name='Antenna Material')
mat_antenna.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_light = bpy.data.materials.new(name='Light Material')
mat_light.diffuse_color = (0, 1, 0, 1)

# Function to create a scaled cube

def create_body(location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    body = bpy.context.object
    body.scale = scale
    body.name = 'Router Base'
    body.data.materials.append(mat_body)

# Function to create an antenna

def create_antenna(x_position):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_position, 0, 1.2))
    antenna = bpy.context.object
    antenna.name = f'Antenna at {x_position}'
    antenna.data.materials.append(mat_antenna)

# Function to create a light

def create_light(x_position):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_position, 1.1, 0.6))
    light = bpy.context.object
    light.name = f'Indicator Light at {x_position}'
    light.data.materials.append(mat_light)

# Create the body with specific scaling
create_body(location=(0, 0, 0.5), scale=(2, 1, 0.2))

# Generate antennas
for index in range(3):
    create_antenna(x_position=(index - 1) * 1.5)

# Generate indicator lights
for index in range(3):
    create_light(x_position=(index - 1) * 0.5)


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
