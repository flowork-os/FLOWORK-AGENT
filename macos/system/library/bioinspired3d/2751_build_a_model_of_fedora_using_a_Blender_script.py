# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_fedora_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of fedora using a Blender script

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the model
material_hat = bpy.data.materials.new(name='HatColor')
material_hat.diffuse_color = (0.2, 0.2, 0.2, 1)
material_ribbon = bpy.data.materials.new(name='RibbonColor')
material_ribbon.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create the hat components
brim = bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.1, location=(0, 0, 0))
brim_object = bpy.context.object
brim_object.name = 'Brim'
brim_object.data.materials.append(material_hat)

crown = bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=1, location=(0, 0, 0.55))
crown_object = bpy.context.object
crown_object.name = 'Crown'
crown_object.data.materials.append(material_hat)

# Create and apply a boolean modifier for the indentation
bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0, depth=0.6, location=(0, 0, 1.1))
indentation_object = bpy.context.object
indentation_object.name = 'Indentation'
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers['Boolean'].operation = 'DIFFERENCE'
bpy.context.object.modifiers['Boolean'].object = crown_object
bpy.ops.object.modifier_apply(modifier='Boolean')
bpy.data.objects.remove(indentation_object)

# Create the ribbon
ribbon = bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 0.55))
ribbon_object = bpy.context.object
ribbon_object.name = 'Ribbon'
ribbon_object.data.materials.append(material_ribbon)


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
