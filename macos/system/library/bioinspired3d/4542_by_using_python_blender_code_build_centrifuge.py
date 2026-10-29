# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code_build_centrifuge" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code build centrifuge

import bpy
import math

# Begin by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material properties for various components
body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.5, 0.5, 0.5, 1)

lid_material = bpy.data.materials.new(name='Lid Material')
lid_material.diffuse_color = (0.7, 0.7, 0.7, 1)

panel_material = bpy.data.materials.new(name='Control Panel Material')
panel_material.diffuse_color = (0.2, 0.2, 0.2, 1)

button_material = bpy.data.materials.new(name='Button Material')
button_material.diffuse_color = (0, 0, 1, 1)

screen_material = bpy.data.materials.new(name='Screen Material')
screen_material.diffuse_color = (0, 1, 0, 1)

# Create body
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
body = bpy.context.object
body.name = 'Centrifuge Body'
body.data.materials.append(body_material)

# Create lid
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.2, location=(0, 0, 1.5))
lid = bpy.context.object
lid.name = 'Centrifuge Lid'
lid.data.materials.append(lid_material)

# Create control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1.1, 0.75))
panel = bpy.context.object
panel.name = 'Control Panel'
panel.scale[2] = 0.1
panel.data.materials.append(panel_material)

# Create buttons using a loop
for idx in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.15 + idx * 0.15, 1.15, 0.75))
    button = bpy.context.object
    button.name = f'Button {idx + 1}'
    button.data.materials.append(button_material)

# Create display screen
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.3, 1.15, 0.75))
screen = bpy.context.object
screen.name = 'Display Screen'
screen.scale[2] = 0.05
screen.data.materials.append(screen_material)

# Create slots for test tubes
for idx in range(6):
    angle = math.radians(idx * 60)
    x = 0.5 * math.cos(angle)
    y = 0.5 * math.sin(angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(x, y, 0.25))
    slot = bpy.context.object
    slot.name = f'Test Tube Slot {idx + 1}'
    slot.data.materials.append(body_material)


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
