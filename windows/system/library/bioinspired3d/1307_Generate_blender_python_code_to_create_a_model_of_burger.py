# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_to_create_a_model_of_burger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code to create a model of burger.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create new materials for the burger components
materials = {
    'bun': (0.8, 0.6, 0.4, 1),  # Light brown
    'patty': (0.4, 0.2, 0.1, 1),  # Dark brown
    'lettuce': (0.2, 0.8, 0.2, 1),  # Green
    'cheese': (1, 0.9, 0, 1)  # Yellow
}

# Function to add a cube

def add_cube(size, loc, name, color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = 0.05
    mat = bpy.data.materials.new(name=color)
    mat.diffuse_color = materials[color]
    cube.data.materials.append(mat)
    return cube

# Function to add a cylinder

def add_cylinder(radius, depth, loc, name, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    cylinder = bpy.context.object
    cylinder.name = name
    mat = bpy.data.materials.new(name=color)
    mat.diffuse_color = materials[color]
    cylinder.data.materials.append(mat)
    return cylinder

# Create each burger layer
bottom_bun = add_cylinder(1, 0.3, (0, 0, 0), 'Bottom Bun', 'bun')
patty = add_cylinder(0.9, 0.2, (0, 0, 0.25), 'Patty', 'patty')
cheese = add_cube(1.8, (0, 0, 0.45), 'Cheese', 'cheese')
lettuce = add_cylinder(1, 0.1, (0, 0, 0.55), 'Lettuce', 'lettuce')
top_bun = add_cylinder(1, 0.3, (0, 0, 0.75), 'Top Bun', 'bun')


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
