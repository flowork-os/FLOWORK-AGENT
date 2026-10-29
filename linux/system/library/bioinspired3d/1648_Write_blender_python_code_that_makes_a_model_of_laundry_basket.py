# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_makes_a_model_of_laundry_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that makes a model of laundry basket

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize the material for the basket
material_basket = bpy.data.materials.new(name="Basket Color")
material_basket.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray color

# Function to create basket body
def create_basket_body():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    basket = bpy.context.object
    basket.name = "Basket"
    basket.scale = (1, 0.7, 0.5)
    basket.data.materials.append(material_basket)

# Function to create handles
def create_handles():
    positions = [(-1.2, 0, 1.2), (1.2, 0, 1.2)]
    for pos in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=pos, rotation=(0, 1.57, 0))
        handle = bpy.context.object
        handle.name = "Basket Handle"
        handle.data.materials.append(material_basket)

create_basket_body()
create_handles()


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
