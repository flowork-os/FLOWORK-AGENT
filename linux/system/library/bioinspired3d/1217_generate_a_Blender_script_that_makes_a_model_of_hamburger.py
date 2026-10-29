# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_that_makes_a_model_of_hamburger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script that makes a model of hamburger

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the burger components
bun_material = bpy.data.materials.new(name="Bun")
bun_material.diffuse_color = (0.85, 0.55, 0.35, 1)
patty_material = bpy.data.materials.new(name="Patty")
patty_material.diffuse_color = (0.35, 0.15, 0.05, 1)
lettuce_material = bpy.data.materials.new(name="Lettuce")
lettuce_material.diffuse_color = (0.1, 0.9, 0.1, 1)
tomato_material = bpy.data.materials.new(name="Tomato")
tomato_material.diffuse_color = (0.9, 0.2, 0.2, 1)
cheese_material = bpy.data.materials.new(name="Cheese")
cheese_material.diffuse_color = (1, 0.9, 0.2, 1)

# Create burger components as functions

def create_burger_part(shape, radius, depth, position, name, material):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    elif shape == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=radius * 2, location=position)
    part = bpy.context.object
    part.name = name
    part.data.materials.append(material)

# Construct the burger
create_burger_part('cylinder', 1, 0.2, (0, 0, 0), "Bottom Bun", bun_material)
create_burger_part('cylinder', 0.9, 0.2, (0, 0, 0.2), "Beef Patty", patty_material)
create_burger_part('cylinder', 1, 0.05, (0, 0, 0.35), "Lettuce", lettuce_material)
create_burger_part('cylinder', 0.9, 0.05, (0, 0, 0.4), "Tomato Slice 1", tomato_material)
create_burger_part('cylinder', 0.9, 0.05, (0, 0, 0.45), "Tomato Slice 2", tomato_material)

# Create cheese slice
create_burger_part('cube', 0.9, 0.025, (0, 0, 0.525), "Cheese Slice", cheese_material)
create_burger_part('cylinder', 1, 0.2, (0, 0, 0.65), "Top Bun", bun_material)


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
