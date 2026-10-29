# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_constructs_a_model_of_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that constructs a model of coffee grinder.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name='Metallic')
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
wood_material = bpy.data.materials.new(name='Wooden')
wood_material.diffuse_color = (0.54, 0.27, 0.07, 1)

# Function to create a cone

def create_cone(location, radius_top, radius_bottom, height, name, material):
    bpy.ops.mesh.primitive_cone_add(radius1=radius_top, radius2=radius_bottom, depth=height, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Function to create a cylinder

def create_cylinder(location, radius, height, name, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the Hopper
hopper = create_cone((0, 0, 1.2), 0.3, 0.1, 0.4, 'Hopper', metal_material)

# Create the Grinding Mechanism
grinding_mechanism = create_cylinder((0, 0, 0.75), 0.25, 0.5, 'Grinding Mechanism', metal_material)

# Create the Container
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.25))
container = bpy.context.object
container.name = 'Container'
container.data.materials.append(wood_material)

# Create the Handle
handle = create_cylinder((0.35, 0, 0.75), 0.05, 0.8, 'Handle', metal_material, rotation=(0, math.pi/2, 0))

# Create the Handle Knob
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.75, 0, 0.75))
handle_knob = bpy.context.object
handle_knob.name = 'Handle Knob'
handle_knob.data.materials.append(wood_material)


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
