# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_building_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for building dog bowl

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the bowl and kibble
material_bowl = bpy.data.materials.new(name='BowlMaterial')
material_bowl.diffuse_color = (0.8, 0.3, 0.1, 1)
material_kibble = bpy.data.materials.new(name='KibbleMaterial')
material_kibble.diffuse_color = (0.6, 0.4, 0.2, 1)

# Create bowl and dip using a function

def add_cylinder(radius, height, position, label, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = label
    obj.data.materials.append(mat)
    return obj

# Generate bowl and dip
bowl_object = add_cylinder(1, 0.5, (0, 0, 0), 'Bowl', material_bowl)
dip_object = add_cylinder(0.8, 0.4, (0, 0, 0.05), 'Dip', material_bowl)

# Boolean operation to create dip in the bowl
bool_modifier = bowl_object.modifiers.new(type='BOOLEAN', name='BooleanOp')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = dip_object
bpy.context.view_layer.objects.active = bowl_object
bpy.ops.object.modifier_apply(modifier='BooleanOp')
bpy.data.objects.remove(dip_object)

# Function to create kibble

def create_kibble_piece(index):
    x_coord = 0.5 * (index % 2) - 0.25
    y_coord = 0.5 * (index // 2) - 0.25
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(x_coord, y_coord, 0.1))
    kibble_piece = bpy.context.object
    kibble_piece.name = f'KibblePiece_{index + 1}'
    kibble_piece.data.materials.append(material_kibble)

# Create kibble pieces
for idx in range(5):
    create_kibble_piece(idx)


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
