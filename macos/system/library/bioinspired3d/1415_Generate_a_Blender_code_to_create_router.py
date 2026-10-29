# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_to_create_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code to create router.

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
mat_black = bpy.data.materials.new(name="Matte Black")
mat_black.diffuse_color = (0.0, 0.0, 0.0, 1)
mat_green = bpy.data.materials.new(name="Vibrant Green")
mat_green.diffuse_color = (0.0, 1.0, 0.0, 1)

# Function to create a cube for the router body

def create_router_body(size, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    body = bpy.context.object
    body.name = "Router Base"
    body.scale = scale
    body.data.materials.append(mat_black)
    return body

# Step 2: Build the router body
router_body = create_router_body(2, (0, 0, 0.5), (1.5, 1, 0.2))

# Function to create antennae

def create_antennae(count):
    for i in range(count):
        x_position = 0.7 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_position, -0.5, 1))
        antenna = bpy.context.object
        antenna.name = f"Antenna_{i + 1}"
        antenna.data.materials.append(mat_black)

# Step 3: Add antennae
create_antennae(2)

# Function to create LED indicators

def create_leds(count):
    for i in range(count):
        x_position = -0.6 + i * 0.3
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_position, 1.1, 0.6))
        led = bpy.context.object
        led.name = f"LED_Light_{i + 1}"
        led.data.materials.append(mat_green)

# Step 4: Place LED indicator lights
create_leds(5)


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
