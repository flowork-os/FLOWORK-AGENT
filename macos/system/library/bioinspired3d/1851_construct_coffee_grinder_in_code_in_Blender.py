# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_coffee_grinder_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct coffee grinder in code in Blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

metal_material = create_material('Metal Surface', (0.5, 0.5, 0.5, 1))
wood_material = create_material('Wood Finish', (0.55, 0.27, 0.07, 1))

def create_cylinder(radius, height, position, object_name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = object_name
    obj.data.materials.append(material)

create_cylinder(1, 2, (0, 0, 1), 'Grinder Body', metal_material)
create_cylinder(0.9, 1.8, (0, 0, 2.1), 'Bean Compartment', wood_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(0, 1.1, 1.5), rotation=(1.57, 0, 0))
handle = bpy.context.object
handle.name = 'Grinder Handle'
handle.data.materials.append(metal_material)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 1.5, 1.5))
knob = bpy.context.object
knob.name = 'Knob for Handle'
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
