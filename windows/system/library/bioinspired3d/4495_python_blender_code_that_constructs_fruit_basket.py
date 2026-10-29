# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_constructs_fruit_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that constructs fruit basket.

import bpy

# Clear the scene before creating a new model
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the basket with a different shade
basket_material = bpy.data.materials.new(name='BasketShade')
basket_material.diffuse_color = (0.4, 0.2, 0.05, 1)  # A different brown tone

# Create the base and walls of the basket using a function

def add_cylinder(r, h, loc, obj_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(basket_material)
    return obj

# Step 2: Construct the base and walls
base = add_cylinder(1, 0.2, (0, 0, 0), 'BasketBase')
walls = add_cylinder(1, 1, (0, 0, 0.6), 'BasketWalls')

# Step 4: Create an inner cylinder for the hollow effect
inner_cyl = add_cylinder(0.9, 1.2, (0, 0, 0.6), 'InnerWall')

# Use Boolean modifier to hollow out the walls
hollow_mod = walls.modifiers.new(name='HollowOut', type='BOOLEAN')
hollow_mod.operation = 'DIFFERENCE'
hollow_mod.object = inner_cyl
bpy.context.view_layer.objects.active = walls
bpy.ops.object.modifier_apply(modifier='HollowOut')

# Clean up the inner cylinder object
bpy.data.objects.remove(inner_cyl, do_unlink=True)


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
