# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_that_makes_a_model_of_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script that makes a model of dog bowl.

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the bowl with a functional approach
def create_hollow_bowl():
    # Create the outer bowl
    bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.5, location=(0, 0, 0))
    bowl_outer = bpy.context.object
    bowl_outer.name = 'HollowBowlOuter'

    # Create the inner bowl
    bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.4, location=(0, 0, 0.05))
    bowl_inner = bpy.context.object
    bowl_inner.name = 'HollowBowlInner'

    # Apply boolean modifier to create hollow effect
    boolean_modifier = bowl_outer.modifiers.new(type='BOOLEAN', name='HollowBoolean')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = bowl_inner
    bpy.context.view_layer.objects.active = bowl_outer
    bpy.ops.object.modifier_apply(modifier='HollowBoolean')

    # Delete the inner bowl
    bpy.data.objects.remove(bowl_inner, do_unlink=True)

    # Add material to the outer bowl
    bowl_material = bpy.data.materials.new(name='HollowBowlMaterial')
    bowl_material.diffuse_color = (0.8, 0.8, 0.2, 1)  # Yellow color
    bowl_outer.data.materials.append(bowl_material)

create_hollow_bowl()


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
