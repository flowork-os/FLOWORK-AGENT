# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script_construct_dog_house" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script construct dog house

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material Definitions
roof_material = bpy.data.materials.new(name='Roof Material')
roof_material.diffuse_color = (0.55, 0.27, 0.07, 1)
body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.75, 0.75, 0.75, 1)
entrance_material = bpy.data.materials.new(name='Entrance Material')
entrance_material.diffuse_color = (0, 0, 0, 1)
window_material = bpy.data.materials.new(name='Window Material')
window_material.diffuse_color = (0.5, 0.5, 0.5, 1)
nameplate_material = bpy.data.materials.new(name='Nameplate Material')
nameplate_material.diffuse_color = (0.9, 0.7, 0.4, 1)
bowl_material = bpy.data.materials.new(name='Bowl Material')
bowl_material.diffuse_color = (0.8, 0.1, 0.1, 1)
toy_material = bpy.data.materials.new(name='Toy Material')
toy_material.diffuse_color = (0.1, 0.8, 0.1, 1)

# Function to create a mesh object
def create_mesh(shape, location, scale, material):
    if shape == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=scale[0], location=location)
    elif shape == 'cone':
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=scale[0], depth=scale[1], location=location, rotation=(0, 0, math.pi/4))
    elif shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=scale[0], depth=scale[1], location=location)
    elif shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=scale[0], location=location)
    obj = bpy.context.object
    obj.data.materials.append(material)
    return obj

# Create the Body
body = create_mesh('cube', (0, 0, 1), (2, 2, 2), body_material)
body.name = 'Body'

# Create the Roof
roof = create_mesh('cone', (0, 0, 2.5), (1.5, 1, 1), roof_material)
roof.name = 'Roof'

# Create the Entrance
entrance = create_mesh('cube', (0, -1, 0.5), (0.8, 0.1, 0.1), entrance_material)
entrance.name = 'Entrance'

# Create the Window
window = create_mesh('cube', (1, 0, 1.5), (0.4, 0.1, 0.1), window_material)
window.name = 'Window'

# Create the Nameplate
nameplate = create_mesh('cube', (0, -1.1, 1.8), (0.6, 0.05, 0.1), nameplate_material)
nameplate.name = 'Nameplate'

# Create the Dog Bowl
bowl = create_mesh('cylinder', (-1, -1, 0.1), (0.3, 0.2, 0.2), bowl_material)
bowl.name = 'Dog Bowl'

# Create the Chew Toy
chew_toy = create_mesh('sphere', (1, -1, 0.2), (0.2, 0.2, 0.2), toy_material)
chew_toy.name = 'Chew Toy'


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
