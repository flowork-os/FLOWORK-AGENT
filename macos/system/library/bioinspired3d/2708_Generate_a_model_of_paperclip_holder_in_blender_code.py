# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_paperclip_holder_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of paperclip holder in blender code

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a gray material
material = bpy.data.materials.new(name="Gray")
material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Helper function to build the cylinder

def create_cylinder(radius, height, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Generate the base and holder
base_cylinder = create_cylinder(1.5, 0.2, (0, 0, 0), "Base")
holder_cylinder = create_cylinder(1.4, 2, (0, 0, 1.1), "Holder")

# Create the inner cylinder for the boolean operation
inner_cylinder = create_cylinder(1.3, 2, (0, 0, 1.1), "Inner")

# Add a boolean modifier to the holder
boolean_mod = holder_cylinder.modifiers.new(name="Boolean Modifier", type='BOOLEAN')
boolean_mod.operation = 'DIFFERENCE'
boolean_mod.object = inner_cylinder
bpy.context.view_layer.objects.active = holder_cylinder
bpy.ops.object.modifier_apply(modifier="Boolean Modifier")
bpy.data.objects.remove(inner_cylinder)


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
