# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_code_that_makes_a_model_of_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender code that makes a model of coffee grinder

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name='Metal Material')
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to add a cylinder
def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create Grinder Body
body = add_cylinder(1, 2, (0, 0, 1), 'Grinder Body', metal_material)
# Create Bean Compartment
bean_compartment = add_cylinder(0.9, 1.8, (0, 0, 2.1), 'Bean Compartment', wood_material)

# Create Handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(0, 1.1, 1.5), rotation=(1.57, 0, 0))
handle = bpy.context.object
handle.name = 'Handle'
handle.data.materials.append(metal_material)

# Create Handle Knob
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 1.5, 1.5))
knob = bpy.context.object
knob.name = 'Handle Knob'
knob.data.materials.append(wood_material)


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
