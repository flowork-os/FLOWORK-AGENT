# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_code_in_Blender_to_create_a_model_of_paperclip_holder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write code in Blender to create a model of paperclip holder

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the object
material_gray = bpy.data.materials.new(name="Material_Gray")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder
def add_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_gray)
    return obj

# Constructing the base and holder
base_object = add_cylinder(1.5, 0.2, (0, 0, 0), "Base")
holder = add_cylinder(1.4, 2, (0, 0, 1.1), "Holder")

# Create inner space
inner_cylinder = add_cylinder(1.3, 2, (0, 0, 1.1), "Inner_Cylinder")

# Set up and apply the boolean modifier
bool_modifier = holder.modifiers.new(name="Subtract_Inner", type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_cylinder
bpy.context.view_layer.objects.active = holder
bpy.ops.object.modifier_apply(modifier="Subtract_Inner")
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
