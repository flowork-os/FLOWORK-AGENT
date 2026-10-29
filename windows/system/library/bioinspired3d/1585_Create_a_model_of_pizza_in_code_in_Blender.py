# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_pizza_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of pizza in code in Blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
materials = {
    'Crust': (0.76, 0.60, 0.42, 1),
    'Cheese': (1.0, 0.9, 0.4, 1),
    'Pepperoni': (0.8, 0.1, 0.1, 1)
}

for mat_name, color in materials.items():
    mat = bpy.data.materials.new(name=mat_name)
    mat.diffuse_color = color

# Create the crust
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.1, location=(0, 0, 0))
crust_object = bpy.context.object
crust_object.name = 'Crust'
crust_object.data.materials.append(bpy.data.materials['Crust'])

# Create cheese layer
bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=0.02, location=(0, 0, 0.06))
cheese_object = bpy.context.object
cheese_object.name = 'Cheese'
cheese_object.data.materials.append(bpy.data.materials['Cheese'])

# Generate pepperoni slices
pepperoni_coords = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5)]
for idx, coord in enumerate(pepperoni_coords):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.02, location=(coord[0], coord[1], 0.08))
    pepperoni_obj = bpy.context.object
    pepperoni_obj.name = f'Pepperoni_Slice_{idx + 1}'
    pepperoni_obj.data.materials.append(bpy.data.materials['Pepperoni'])


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
