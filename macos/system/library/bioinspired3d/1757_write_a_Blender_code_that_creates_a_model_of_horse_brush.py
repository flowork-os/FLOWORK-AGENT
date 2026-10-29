# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_creates_a_model_of_horse_brush" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that creates a model of horse brush.

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the brush and bristles
brush_material = bpy.data.materials.new(name='BrushMaterial')
brush_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown brush color
bristle_material = bpy.data.materials.new(name='BristleMaterial')
bristle_material.diffuse_color = (0.33, 0.33, 0.33, 1)  # Dark gray bristle color

# Function to create the brush components
def create_cylinder(radius, depth, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the brush base
base = create_cylinder(1, 0.2, (0, 0, 0), 'BrushBase', brush_material)

# Create the bristles
bristles = create_cylinder(0.9, 0.3, (0, 0, 0.25), 'Bristles', bristle_material)

# Create the strap as a cube and adjust its dimensions
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0.2))
strap = bpy.context.object
strap.scale = (2, 0.1, 0.1)
strap.name = 'Strap'
strap.data.materials.append(brush_material)


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
