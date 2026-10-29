# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_dog_house_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of dog house in Blender Python script

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material creation function

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Define materials
roof_mat = create_material('Roof Material', (0.55, 0.27, 0.07, 1))
body_mat = create_material('Body Material', (0.75, 0.75, 0.75, 1))
entrance_mat = create_material('Entrance Material', (0, 0, 0, 1))
window_mat = create_material('Window Material', (0.5, 0.5, 0.5, 1))
nameplate_mat = create_material('Nameplate Material', (0.9, 0.7, 0.4, 1))
bowl_mat = create_material('Bowl Material', (0.8, 0.1, 0.1, 1))
toy_mat = create_material('Toy Material', (0.1, 0.8, 0.1, 1))

# Function to create and configure mesh objects

def create_object(type, loc, scale, material):
    if type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=scale[0], location=loc)
    elif type == 'cone':
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=scale[0], depth=scale[1], location=loc, rotation=(0, 0, math.pi/4))
    elif type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=scale[0], depth=scale[1], location=loc)
    elif type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=scale[0], location=loc)
    obj = bpy.context.object
    obj.data.materials.append(material)
    return obj

# Create the components of the model
create_object('cube', (0, 0, 1), (2, 2, 2), body_mat)
create_object('cone', (0, 0, 2.5), (1.5, 1, 1), roof_mat)
create_object('cube', (0, -1, 0.5), (0.8, 0.1, 0.1), entrance_mat)
create_object('cube', (1, 0, 1.5), (0.4, 0.1, 0.1), window_mat)
create_object('cube', (0, -1.1, 1.8), (0.6, 0.05, 0.1), nameplate_mat)
create_object('cylinder', (-1, -1, 0.1), (0.3, 0.2, 0.2), bowl_mat)
create_object('sphere', (1, -1, 0.2), (0.2, 0.2, 0.2), toy_mat)


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
