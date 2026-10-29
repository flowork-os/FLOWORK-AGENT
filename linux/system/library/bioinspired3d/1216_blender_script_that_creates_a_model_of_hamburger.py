# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_creates_a_model_of_hamburger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that creates a model of hamburger.

import bpy

# Start fresh by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Setting up materials for the burger components
materials = {
    'bun': (0.8, 0.6, 0.4, 1),
    'beef': (0.4, 0.2, 0.1, 1),
    'lettuce': (0.2, 0.8, 0.2, 1),
    'tomato': (0.8, 0.1, 0.1, 1),
    'cheese': (1, 0.8, 0.1, 1)
}

# Function to add a colored mesh

def add_mesh_primitive(primitive_type, params, name, color):
    if primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif primitive_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name
    mat = bpy.data.materials.new(name=name + " Material")
    mat.diffuse_color = color
    obj.data.materials.append(mat)

# Create burger layers
add_mesh_primitive('cylinder', (1, 0.2, (0, 0, 0)), "Bottom Bun", materials['bun'])
add_mesh_primitive('cylinder', (0.9, 0.2, (0, 0, 0.2)), "Beef Patty", materials['beef'])
add_mesh_primitive('cylinder', (1, 0.05, (0, 0, 0.35)), "Lettuce", materials['lettuce'])
add_mesh_primitive('cylinder', (0.9, 0.05, (0, 0, 0.4)), "Tomato Slice 1", materials['tomato'])
add_mesh_primitive('cylinder', (0.9, 0.05, (0, 0, 0.45)), "Tomato Slice 2", materials['tomato'])

# Create cheese
add_mesh_primitive('cube', (1.8, (0, 0, 0.525)), "Cheese Slice", materials['cheese'])
cheese_slice = bpy.context.object
cheese_slice.scale[2] = 0.025

add_mesh_primitive('cylinder', (1, 0.2, (0, 0, 0.65)), "Top Bun", materials['bun'])


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
