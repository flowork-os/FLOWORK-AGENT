# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_generate_food_processor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to generate food processor.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with unique colors
material_dark = bpy.data.materials.new(name='Dark Material')
material_dark.diffuse_color = (0.2, 0.2, 0.2, 1)
material_light = bpy.data.materials.new(name='Light Material')
material_light.diffuse_color = (1, 1, 1, 0.1)
material_gray = bpy.data.materials.new(name='Gray Material')
material_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
material_red = bpy.data.materials.new(name='Red Material')
material_red.diffuse_color = (0.8, 0, 0, 1)

# Create the base cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_cube = bpy.context.object
base_cube.scale = (1, 1, 0.5)
base_cube.name = 'Base'
base_cube.data.materials.append(material_dark)

# Create the main container
bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=1.5, location=(0, 0, 1.75))
main_container = bpy.context.object
main_container.name = 'Container'
main_container.data.materials.append(material_light)

# Create the lid for the container
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=0.1, location=(0, 0, 2.5))
container_lid = bpy.context.object
container_lid.name = 'Lid'
container_lid.data.materials.append(material_gray)

# Add a feed tube to the lid
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.5, location=(0, 0, 2.75))
feed_tube = bpy.context.object
feed_tube.name = 'Feed Tube'
feed_tube.data.materials.append(material_gray)

# Create a control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1.05, 0.25))
control_panel = bpy.context.object
control_panel.scale = (1, 0.1, 0.5)
control_panel.name = 'Control Panel'
control_panel.data.materials.append(material_dark)

# Add buttons to the control panel
for i in range(3):
    button_position = (-0.2 + i * 0.2, 1.1, 0.25)
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=button_position)
    button = bpy.context.object
    button.name = f'Button {i + 1}'
    button.data.materials.append(material_red)


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
