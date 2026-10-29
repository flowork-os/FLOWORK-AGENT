# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_pencil_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of pencil in Blender Python script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the pencil components
materials = {
    'yellow': (1, 1, 0, 1),
    'pink': (1, 0.75, 0.8, 1),
    'gray': (0.5, 0.5, 0.5, 1),
    'wood': (0.8, 0.52, 0.25, 1)
}

# Function to add material to a new object

def add_material(obj, color):
    mat = bpy.data.materials.new(name=color)
    mat.diffuse_color = materials[color]
    obj.data.materials.append(mat)

# Function to create and configure the pencil components

def create_pencil():
    # Pencil body
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.1, depth=2, location=(0, 0, 1))
    pencil_body = bpy.context.object
    pencil_body.name = 'Pencil Body'
    add_material(pencil_body, 'yellow')

    # Sharpened tip
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.1, radius2=0, depth=0.3, location=(0, 0, 2.15))
    sharpened_tip = bpy.context.object
    sharpened_tip.name = 'Sharpened Tip'
    add_material(sharpened_tip, 'wood')

    # Eraser holder
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.11, depth=0.1, location=(0, 0, 0.05))
    eraser_holder = bpy.context.object
    eraser_holder.name = 'Eraser Holder'
    add_material(eraser_holder, 'gray')

    # Eraser
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.1, depth=0.1, location=(0, 0, -0.05))
    eraser = bpy.context.object
    eraser.name = 'Eraser'
    add_material(eraser, 'pink')

create_pencil()


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
