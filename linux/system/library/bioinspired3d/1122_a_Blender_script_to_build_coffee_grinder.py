# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_build_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to build coffee grinder

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
material_metal = bpy.data.materials.new(name="Shiny Metal")
material_metal.diffuse_color = (0.5, 0.5, 0.5, 1)
material_wood = bpy.data.materials.new(name="Natural Wood")
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to add a new mesh object
def add_mesh_object(mesh_type, location, rotation=(0, 0, 0), **kwargs):
    if mesh_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    elif mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(location=location, **kwargs)
    elif mesh_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(location=location, radius=0.1)

# Create the main components
add_mesh_object('cube', location=(0, 0, 1))
base_mesh = bpy.context.object
base_mesh.name = "Base"
base_mesh.data.materials.append(material_wood)

add_mesh_object('cylinder', location=(0, 0, 2.75), radius=0.75, depth=1.5)
bean_container = bpy.context.object
bean_container.name = "Bean Container"
bean_container.data.materials.append(material_metal)

add_mesh_object('cylinder', location=(0, 0, 3.55), radius=0.2, depth=0.1)
ground_knob = bpy.context.object
ground_knob.name = "Grind Setting Knob"
ground_knob.data.materials.append(material_metal)

add_mesh_object('cylinder', location=(1, 0, 3), radius=0.05, depth=1, rotation=(0, 1.57, 0))
handle_mesh = bpy.context.object
handle_mesh.name = "Handle"
handle_mesh.data.materials.append(material_wood)

add_mesh_object('sphere', location=(1.5, 0, 3))
handle_knob_mesh = bpy.context.object
handle_knob_mesh.name = "Handle Knob"
handle_knob_mesh.data.materials.append(material_wood)


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
