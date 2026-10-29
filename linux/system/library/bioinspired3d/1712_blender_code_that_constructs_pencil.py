# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_constructs_pencil" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that constructs pencil.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for pencil and eraser
material_wood = bpy.data.materials.new(name='Wood Texture')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)
material_eraser = bpy.data.materials.new(name='Eraser Color')
material_eraser.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a mesh object
def create_mesh_object(mesh_type, params, name, material):
    if mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**params)
    elif mesh_type == 'cone':
        bpy.ops.mesh.primitive_cone_add(**params)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create pencil body
create_mesh_object('cylinder', {'radius': 0.05, 'depth': 2, 'location': (0, 0, 1)}, 'Pencil Body', material_wood)

# Create pencil tip
create_mesh_object('cone', {'vertices': 32, 'radius1': 0.05, 'radius2': 0.01, 'depth': 0.2, 'location': (0, 0, 2.1)}, 'Pencil Tip', material_wood)

# Create eraser
create_mesh_object('cylinder', {'radius': 0.05, 'depth': 0.1, 'location': (0, 0, 0.05)}, 'Eraser', material_eraser)


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
