# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_constructs_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that constructs a model of bird feeder

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize wood material with a specific color
material_wood = bpy.data.materials.new(name='WoodColor')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Define a function to create a cone
def create_cone(radius, height, position, name):
    bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=height, location=position)
    cone = bpy.context.object
    cone.name = name
    cone.data.materials.append(material_wood)
    return cone

# Create base and stand using cylinders
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
base = bpy.context.object
base.name = 'Base'
base.data.materials.append(material_wood)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0, 0, 0.55))
stand = bpy.context.object
stand.name = 'Stand'
stand.data.materials.append(material_wood)

bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.1, location=(0, 0, 1.1))
tray = bpy.context.object
tray.name = 'Feeder Tray'
tray.data.materials.append(material_wood)

# Finally, create the roof using the cone function
create_cone(0.5, 0.3, (0, 0, 1.35), 'Roof')


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
