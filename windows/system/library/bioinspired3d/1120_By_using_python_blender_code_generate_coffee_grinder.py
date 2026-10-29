# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_generate_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code generate coffee grinder

import bpy

# Clear the entire scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name="Metallic")
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Lighter gray color
wood_material = bpy.data.materials.new(name="Wooden")
wood_material.diffuse_color = (0.54, 0.25, 0.05, 1)  # Darker brown color

# Function to create a primitive object

def create_primitive(shape, **kwargs):
    if shape == 'cube':
        bpy.ops.mesh.primitive_cube_add(**kwargs)
    elif shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    elif shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(**kwargs)

# Build the base
create_primitive('cube', size=2, location=(0, 0, 1))
base_object = bpy.context.object
base_object.name = "Base"
base_object.data.materials.append(wood_material)

# Create the bean container
create_primitive('cylinder', radius=0.75, depth=1.5, location=(0, 0, 2.75))
container_object = bpy.context.object
container_object.name = "Bean Container"
container_object.data.materials.append(metal_material)

# Add the grind setting knob
create_primitive('cylinder', radius=0.2, depth=0.1, location=(0, 0, 3.55))
knob_object = bpy.context.object
knob_object.name = "Grind Setting Knob"
knob_object.data.materials.append(metal_material)

# Create the handle
create_primitive('cylinder', radius=0.05, depth=1, location=(1, 0, 3), rotation=(0, 1.57, 0))
handle_object = bpy.context.object
handle_object.name = "Handle"
handle_object.data.materials.append(wood_material)

# Add the handle knob
create_primitive('sphere', radius=0.1, location=(1.5, 0, 3))
handle_knob_object = bpy.context.object
handle_knob_object.name = "Handle Knob"
handle_knob_object.data.materials.append(wood_material)


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
