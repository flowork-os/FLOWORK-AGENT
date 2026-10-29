# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_create_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to create bird feeder

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the structure
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(wood_material)
    return obj

# Construct the base, stand, tray, and roof
base = create_cylinder(0.5, 0.1, (0, 0, 0), 'Base')
stand = create_cylinder(0.05, 1, (0, 0, 0.55), 'Stand')
tray = create_cylinder(0.4, 0.1, (0, 0, 1.1), 'Feeder Tray')

# Create the roof using a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=0.3, location=(0, 0, 1.35))
roof = bpy.context.object
roof.name = 'Roof'
roof.data.materials.append(wood_material)


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
