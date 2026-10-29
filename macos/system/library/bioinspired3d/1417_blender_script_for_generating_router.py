# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_generating_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for generating router.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the router
black_material = bpy.data.materials.new(name="Deep Black")
black_material.diffuse_color = (0.0, 0.0, 0.0, 1)
green_material = bpy.data.materials.new(name="Bright Green")
green_material.diffuse_color = (0.0, 1.0, 0.0, 1)

# Function to create the router body

def add_router_body():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    router = bpy.context.object
    router.name = "Router_Main"
    router.scale = (1.5, 1, 0.2)
    router.data.materials.append(black_material)

# Create the router body
add_router_body()

# Function to create antennae

def add_antennae():
    for i in range(2):
        x_coord = 0.7 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_coord, -0.5, 1))
        antenna = bpy.context.object
        antenna.name = f"Antenna_{i + 1}"
        antenna.data.materials.append(black_material)

# Add antennae
add_antennae()

# Function to create LED lights

def add_leds():
    for i in range(5):
        x_coord = -0.6 + i * 0.3
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_coord, 1.1, 0.6))
        led = bpy.context.object
        led.name = f"LED_{i + 1}"
        led.data.materials.append(green_material)

# Create LED lights
add_leds()


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
