# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_creates_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that creates a model of blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.3, 0.3, 0.3, 1)

button_material = bpy.data.materials.new(name="Control Material")
button_material.diffuse_color = (1, 0, 0, 1)

jar_material = bpy.data.materials.new(name="Container Material")
jar_material.diffuse_color = (1, 1, 1, 0.2)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the base of the jar
base_cylinder = create_cylinder(radius=1, depth=0.5, location=(0, 0, 0.25), name="Base", material=base_material)

# Create the jar
jar_cylinder = create_cylinder(radius=0.8, depth=2, location=(0, 0, 1.5), name="Jar", material=jar_material)

# Function to create buttons
def create_button(index):
    x_position = -0.5 + (index * 0.5)
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(x_position, 0.9, 0.15))
    button = bpy.context.object
    button.name = f"Control {index + 1}"
    button.data.materials.append(button_material)

# Create control buttons
for button_index in range(3):
    create_button(button_index)


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
