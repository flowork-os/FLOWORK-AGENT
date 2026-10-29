# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_building_centrifuge" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for building centrifuge.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the centrifuge components
materials = {
    'body': (0.5, 0.5, 0.5, 1),
    'lid': (0.7, 0.7, 0.7, 1),
    'panel': (0.2, 0.2, 0.2, 1),
    'button': (0, 0, 1, 1),
    'screen': (0, 1, 0, 1)
}

# Function to create a mesh object with a given type and properties

def create_mesh(primitive_type, location, scale=(1, 1, 1), name='Mesh', material=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=scale[0], depth=scale[1], location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj

# Create materials and assign to variables
body_material = bpy.data.materials.new(name='Body')
body_material.diffuse_color = materials['body']

lid_material = bpy.data.materials.new(name='Lid')
lid_material.diffuse_color = materials['lid']

panel_material = bpy.data.materials.new(name='Panel')
panel_material.diffuse_color = materials['panel']

button_material = bpy.data.materials.new(name='Button')
button_material.diffuse_color = materials['button']

screen_material = bpy.data.materials.new(name='Screen')
screen_material.diffuse_color = materials['screen']

# Construct the centrifuge components
body = create_mesh('cylinder', (0, 0, 0.75), (1, 1.5), 'Centrifuge Body', body_material)
lid = create_mesh('cylinder', (0, 0, 1.5), (1.05, 0.2), 'Centrifuge Lid', lid_material)
panel = create_mesh('cube', (0, 1.1, 0.75), (0.5, 0.1, 0.1), 'Control Panel', panel_material)

# Adjust the scale of the panel
panel.scale[2] = 0.1

# Create buttons on the control panel
for i in range(3):
    button = create_mesh('cube', (-0.15 + i * 0.15, 1.15, 0.75), (0.1, 0.1, 0.1), f'Button {i + 1}', button_material)

# Create the display screen
screen = create_mesh('cube', (0.3, 1.15, 0.75), (0.2, 0.2, 0.05), 'Display Screen', screen_material)

# Create slots for test tubes
for i in range(6):
    angle = math.radians(i * 60)
    x = 0.5 * math.cos(angle)
    y = 0.5 * math.sin(angle)
    create_mesh('cylinder', (x, y, 0.25), (0.1, 0.5), f'Test Tube Slot {i + 1}', body_material)


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
