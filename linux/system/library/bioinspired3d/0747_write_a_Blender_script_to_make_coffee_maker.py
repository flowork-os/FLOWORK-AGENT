# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_to_make_coffee_maker" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script to make coffee maker

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Setup materials
materials = {
    'black': (0.0, 0.0, 0.0, 1),
    'silver': (0.75, 0.75, 0.75, 1),
    'clear': (0.8, 0.8, 0.8, 0.3)
}

# Create the body of the model
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
body = bpy.context.object
body.name = "Main Body"
body.scale = (0.7, 0.5, 1.5)
body.data.materials.append(bpy.data.materials.new(name="Black Material"))
body.data.materials[0].diffuse_color = materials['black']

# Add a carafe
bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.8, location=(0, 0.7, 0.4))
carafe = bpy.context.object
carafe.name = "Carafe"
carafe.data.materials.append(bpy.data.materials.new(name="Silver Material"))
carafe.data.materials[0].diffuse_color = materials['silver']

# Control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0.8, 0, 1.2))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.scale = (0.1, 0.3, 0.4)
control_panel.data.materials.append(bpy.data.materials.new(name="Silver Material"))
control_panel.data.materials[0].diffuse_color = materials['silver']

# Create buttons
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.9, -0.2 + i * 0.2, 1.2))
    button = bpy.context.object
    button.name = f"Button_{i + 1}"
    button.scale = (0.05, 0.05, 0.05)
    button.data.materials.append(bpy.data.materials.new(name="Black Material"))
    button.data.materials[0].diffuse_color = materials['black']

# Water reservoir
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, -0.6, 1.2))
reservoir = bpy.context.object
reservoir.name = "Water Reservoir"
reservoir.scale = (0.6, 0.1, 1.2)
reservoir.data.materials.append(bpy.data.materials.new(name="Clear Material"))
reservoir.data.materials[0].diffuse_color = materials['clear']

# Water level indicator
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.7, 1.2))
indicator = bpy.context.object
indicator.name = "Water Level Indicator"
indicator.scale = (0.05, 0.05, 1)
indicator.data.materials.append(bpy.data.materials.new(name="Black Material"))
indicator.data.materials[0].diffuse_color = materials['black']


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
