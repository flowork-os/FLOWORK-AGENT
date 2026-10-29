# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_construct_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to construct pizza

import bpy

# Clear the scene of any mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the different layers of the pizza
layer1_material = bpy.data.materials.new(name='Layer1')
layer1_material.diffuse_color = (0.8, 0.6, 0.4, 1)
layer2_material = bpy.data.materials.new(name='Layer2')
layer2_material.diffuse_color = (0.8, 0.1, 0.1, 1)
layer3_material = bpy.data.materials.new(name='Layer3')
layer3_material.diffuse_color = (1.0, 0.9, 0.5, 1)

# Function to build a cylinder layer

def build_cylinder(radius, height, position, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(mat)

# Generate the layers of the pizza
build_cylinder(1.1, 0.1, (0, 0, 0), 'PizzaCrust', layer1_material)
build_cylinder(1.0, 0.02, (0, 0, 0.06), 'PizzaSauce', layer2_material)
build_cylinder(0.95, 0.02, (0, 0, 0.08), 'PizzaCheese', layer3_material)


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
