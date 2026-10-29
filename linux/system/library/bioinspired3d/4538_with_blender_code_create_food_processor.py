# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code_create_food_processor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code create food processor.

import bpy

# Clear the mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
materials = {
    'base': (0.2, 0.2, 0.2, 1),
    'container': (1, 1, 1, 0.1),
    'lid': (0.8, 0.8, 0.8, 1),
    'button': (0.8, 0, 0, 1)
}

for mat_name, color in materials.items():
    mat = bpy.data.materials.new(name=mat_name.capitalize() + ' Material')
    mat.diffuse_color = color

# Create the base cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_cube = bpy.context.object
base_cube.scale = (1, 1, 0.5)
base_cube.name = 'Base'
base_cube.data.materials.append(bpy.data.materials['Base Material'])

# Create the container cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=1.5, location=(0, 0, 1.75))
container_cylinder = bpy.context.object
container_cylinder.name = 'Container'
container_cylinder.data.materials.append(bpy.data.materials['Container Material'])

# Create the lid cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=0.1, location=(0, 0, 2.5))
lid_cylinder = bpy.context.object
lid_cylinder.name = 'Lid'
lid_cylinder.data.materials.append(bpy.data.materials['Lid Material'])

# Add the feed tube
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.5, location=(0, 0, 2.75))
feed_tube = bpy.context.object
feed_tube.name = 'Feed Tube'
feed_tube.data.materials.append(bpy.data.materials['Lid Material'])

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1.05, 0.25))
control_panel = bpy.context.object
control_panel.scale = (1, 0.1, 0.5)
control_panel.name = 'Control Panel'
control_panel.data.materials.append(bpy.data.materials['Base Material'])

# Create buttons
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.2 + i * 0.2, 1.1, 0.25))
    button = bpy.context.object
    button.name = f'Button {i + 1}'
    button.data.materials.append(bpy.data.materials['Button Material'])


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
