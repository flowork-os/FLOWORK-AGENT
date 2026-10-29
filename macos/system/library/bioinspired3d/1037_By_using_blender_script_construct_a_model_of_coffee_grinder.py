# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script_construct_a_model_of_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script construct a model of coffee grinder.

import bpy
import math

# Start with a clean scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials
metallic_material = bpy.data.materials.new(name='Shiny Metal')
metallic_material.diffuse_color = (0.5, 0.5, 0.5, 1)
wooden_material = bpy.data.materials.new(name='Dark Wood')
wooden_material.diffuse_color = (0.54, 0.27, 0.07, 1)

# Define geometry creation functions

def add_cone(pos):
    bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.1, depth=0.4, location=pos)
    return bpy.context.object

def add_cylinder(pos, rot):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.5, location=pos, rotation=rot)
    return bpy.context.object

# Create the Hopper
hopper = add_cone((0, 0, 1.2))
hopper.name = 'Hopper'
hopper.data.materials.append(metallic_material)

# Create the Grinding Mechanism
grinder = add_cylinder((0, 0, 0.75), (0, 0, 0))
grinder.name = 'Grinding Mechanism'
grinder.data.materials.append(metallic_material)

# Create the Container
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.25))
container = bpy.context.object
container.name = 'Container'
container.data.materials.append(wooden_material)

# Create the Handle
handle = add_cylinder((0.35, 0, 0.75), (0, math.pi/2, 0))
handle.name = 'Handle'
handle.data.materials.append(metallic_material)

# Create the Handle Knob
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.75, 0, 0.75))
knob = bpy.context.object
knob.name = 'Handle Knob'
knob.data.materials.append(wooden_material)


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
