# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_generating_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for generating a model of pizza

import bpy

# Start with a clean slate
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
material_crust = bpy.data.materials.new(name='Material_Crust')
material_crust.diffuse_color = (0.76, 0.60, 0.42, 1)
material_cheese = bpy.data.materials.new(name='Material_Cheese')
material_cheese.diffuse_color = (1.0, 0.9, 0.4, 1)
material_pepperoni = bpy.data.materials.new(name='Material_Pepperoni')
material_pepperoni.diffuse_color = (0.8, 0.1, 0.1, 1)

# Create the main components
components = [
    (1.5, 0.1, (0, 0, 0), 'Crust', material_crust),
    (1.4, 0.02, (0, 0, 0.06), 'Cheese', material_cheese)
]

for radius, depth, loc, name, mat in components:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)

# Define positions for pepperoni
positions = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5)]
for i, pos in enumerate(positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.02, location=(pos[0], pos[1], 0.08))
    pepperoni_piece = bpy.context.object
    pepperoni_piece.name = f'Pepperoni_{i + 1}'
    pepperoni_piece.data.materials.append(material_pepperoni)


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
