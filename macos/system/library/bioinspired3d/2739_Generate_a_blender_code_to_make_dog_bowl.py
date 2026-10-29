# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_to_make_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code to make dog bowl.

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a bowl with specified parameters

def create_bowl(radius_outer, radius_inner, depth_outer, depth_inner, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_outer, depth=depth_outer, location=location)
    outer_bowl = bpy.context.object
    outer_bowl.name = 'OuterBowl'

    bpy.ops.mesh.primitive_cylinder_add(radius=radius_inner, depth=depth_inner, location=(location[0], location[1], location[2] + 0.05))
    inner_bowl = bpy.context.object
    inner_bowl.name = 'InnerBowl'

    bool_modifier = outer_bowl.modifiers.new(type='BOOLEAN', name='Boolean')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = inner_bowl
    bpy.context.view_layer.objects.active = outer_bowl
    bpy.ops.object.modifier_apply(modifier='Boolean')

    bpy.data.objects.remove(inner_bowl, do_unlink=True)

    return outer_bowl

# Create the bowl
bowl = create_bowl(1.5, 1.3, 0.5, 0.4, (0, 0, 0))

# Assign a new material to the bowl
bowl_material = bpy.data.materials.new(name='BowlColor')
bowl_material.diffuse_color = (0.2, 0.8, 0.2, 1)  # Green color
bowl.data.materials.append(bowl_material)


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
