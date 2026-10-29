# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_router_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate router in a blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
body_material = bpy.data.materials.new(name='Main Body')
body_material.diffuse_color = (0.1, 0.1, 0.1, 1)
led_material = bpy.data.materials.new(name='LED')
led_material.diffuse_color = (0, 1, 0, 1)
port_material = bpy.data.materials.new(name='Port')
port_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Create the body of the router
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
router_body = bpy.context.object
router_body.name = 'Router'
router_body.scale = (2, 1, 0.2)
router_body.data.materials.append(body_material)

# Generate antennas
for i in range(3):
    antenna_x = (i - 1) * 1.5
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(antenna_x, 0, 1.2))
    antenna = bpy.context.object
    antenna.name = f'Antenna_{i + 1}'
    antenna.data.materials.append(body_material)

# Generate LED indicators
for i in range(5):
    led_x = (i - 2) * 0.5
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(led_x, 1.1, 0.6))
    led = bpy.context.object
    led.name = f'LED_{i + 1}'
    led.data.materials.append(led_material)

# Generate ports
for i in range(4):
    port_x = (i - 1.5) * 0.5
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(port_x, -1.1, 0.6))
    port = bpy.context.object
    port.name = f'Port_{i + 1}'
    port.data.materials.append(port_material)


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
