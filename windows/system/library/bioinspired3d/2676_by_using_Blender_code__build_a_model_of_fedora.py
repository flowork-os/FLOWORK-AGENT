# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code__build_a_model_of_fedora" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code, build a model of fedora

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the hat and ribbon
hat_shader = bpy.data.materials.new(name='HatShader')
hat_shader.diffuse_color = (0.2, 0.2, 0.2, 1)
ribbon_shader = bpy.data.materials.new(name='RibbonShader')
ribbon_shader.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create hat elements

def create_hat_element(radius, height, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    element = bpy.context.object
    element.name = name
    element.data.materials.append(material)
    return element

# Generate the brim
brim_part = create_hat_element(1.5, 0.1, (0, 0, 0), 'Brim', hat_shader)

# Generate the crown
crown_part = create_hat_element(0.8, 1, (0, 0, 0.55), 'Crown', hat_shader)

# Create the indentation and apply boolean modifier
bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0, depth=0.6, location=(0, 0, 1.1))
indentation_shape = bpy.context.object
indentation_shape.name = 'Indentation'
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers['Boolean'].operation = 'DIFFERENCE'
bpy.context.object.modifiers['Boolean'].object = crown_part
bpy.ops.object.modifier_apply(modifier='Boolean')
bpy.data.objects.remove(indentation_shape)

# Generate the ribbon
ribbon_part = create_hat_element(0.85, 0.1, (0, 0, 0.55), 'Ribbon', ribbon_shader)


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
