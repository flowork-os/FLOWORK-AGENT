# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_that_creates_a_model_of_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code that creates a model of dog bowl.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bowl and kibble
bowl_material = bpy.data.materials.new(name='BowlMaterial')
bowl_material.diffuse_color = (0.8, 0.3, 0.1, 1)
kibble_material = bpy.data.materials.new(name='KibbleMaterial')
kibble_material.diffuse_color = (0.6, 0.4, 0.2, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the bowl and dip
bowl = create_cylinder(1, 0.5, (0, 0, 0), 'Bowl', bowl_material)
dip = create_cylinder(0.8, 0.4, (0, 0, 0.05), 'Dip', bowl_material)

# Apply boolean modifier for the dip
boolean_modifier = bowl.modifiers.new(type='BOOLEAN', name='BooleanDifference')
boolean_modifier.operation = 'DIFFERENCE'
boolean_modifier.object = dip
bpy.context.view_layer.objects.active = bowl
bpy.ops.object.modifier_apply(modifier='BooleanDifference')
bpy.data.objects.remove(dip)

# Function to create kibble pieces

def create_kibble(index):
    x_position = 0.5 * (index % 2) - 0.25
    y_position = 0.5 * (index // 2) - 0.25
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(x_position, y_position, 0.1))
    kibble_piece = bpy.context.object
    kibble_piece.name = f'Kibble_{index + 1}'
    kibble_piece.data.materials.append(kibble_material)

# Create kibble pieces
for i in range(5):
    create_kibble(i)


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
