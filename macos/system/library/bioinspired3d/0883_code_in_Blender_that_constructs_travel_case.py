# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_constructs_travel_case" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that constructs travel case.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the shapes
light_gray_material = bpy.data.materials.new(name='LightGray')
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)

charcoal_material = bpy.data.materials.new(name='Charcoal')
charcoal_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create toruses

def add_torus(x, y):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.05, location=(x, y, 0))
    torus = bpy.context.object
    torus.name = f'Torus_{x}_{y}'
    torus.data.materials.append(light_gray_material)

# Function to create cylinders

def add_line(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.5, location=(x, y, 0), rotation=(1.5708, 0, 0))
    line = bpy.context.object
    line.name = f'Line_{x}_{y}'
    line.data.materials.append(charcoal_material)
    line.location = (x + 0.5, y + 0.5, 0)

# Create the grid of shapes
for x in range(5):
    for y in range(5):
        add_torus(x, y)
        add_line(x, y)


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
