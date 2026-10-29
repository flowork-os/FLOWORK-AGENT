# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_blender_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of blender using Blender code

import bpy

# Clear the current mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with distinct colors
base_material = bpy.data.materials.new(name='Main Material')
base_material.diffuse_color = (0.2, 0.2, 0.2, 1.0)  # Dark gray
button_material = bpy.data.materials.new(name='Control Material')
button_material.diffuse_color = (0.8, 0.1, 0.1, 1.0)  # Bright red

# Function to create a cylinder base
def create_base():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
    base_object = bpy.context.object
    base_object.name = 'Base'
    base_object.data.materials.append(base_material)

# Function to create the blending jar
def create_jar():
    bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0, depth=2, location=(0, 0, 1.25))
    jar_object = bpy.context.object
    jar_object.name = 'Jar'
    jar_object.data.materials.append(base_material)

# Function to create the button
def create_button():
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0, 0.9, 0.25))
    button_object = bpy.context.object
    button_object.name = 'Button'
    button_object.data.materials.append(button_material)

# Execute creation functions
create_base()
create_jar()
create_button()


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
