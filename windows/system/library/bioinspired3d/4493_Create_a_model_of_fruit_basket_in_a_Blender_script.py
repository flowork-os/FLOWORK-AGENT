# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_fruit_basket_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of fruit basket in a Blender script

import bpy

# Step 1: Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the basket
basket_material = bpy.data.materials.new(name='BasketMaterial')
basket_material.diffuse_color = (0.5, 0.25, 0.1, 1)  # Darker brown

# Step 2: Add the base of the basket
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0))
basket_base = bpy.context.object
basket_base.name = 'Base'
basket_base.data.materials.append(basket_material)

# Step 3: Add the walls of the basket
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0.6))
basket_walls = bpy.context.object
basket_walls.name = 'Walls'
basket_walls.data.materials.append(basket_material)

# Step 4: Create an inner cylinder to hollow out the walls
bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.2, location=(0, 0, 0.6))
inner_cylinder = bpy.context.object
inner_cylinder.name = 'InnerCylinder'

# Apply a boolean modifier to hollow out the basket walls
bool_modifier = basket_walls.modifiers.new(name='Hollow', type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_cylinder
bpy.context.view_layer.objects.active = basket_walls
bpy.ops.object.modifier_apply(modifier='Hollow')

# Cleanup: remove the inner cylinder object
bpy.data.objects.remove(inner_cylinder, do_unlink=True)


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
