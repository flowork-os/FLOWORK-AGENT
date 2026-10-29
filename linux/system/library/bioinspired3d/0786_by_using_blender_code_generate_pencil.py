# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code_generate_pencil" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code generate pencil.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the pencil and eraser
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)
eraser_material = bpy.data.materials.new(name='Eraser Material')
eraser_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a pencil component

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    component = bpy.context.object
    component.name = name
    component.data.materials.append(material)
    return component

# Create pencil body
pencil_body = create_cylinder(radius=0.05, depth=2, location=(0, 0, 1), name='Pencil Body', material=wood_material)

# Create pencil tip
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.05, radius2=0.01, depth=0.2, location=(0, 0, 2.1))
pencil_tip = bpy.context.object
pencil_tip.name = 'Pencil Tip'
pencil_tip.data.materials.append(wood_material)

# Create eraser
create_cylinder(radius=0.05, depth=0.1, location=(0, 0, 0.05), name='Eraser', material=eraser_material)


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
