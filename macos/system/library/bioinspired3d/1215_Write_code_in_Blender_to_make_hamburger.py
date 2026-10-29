# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_to_make_hamburger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender to make hamburger.

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
light_bun_material = bpy.data.materials.new(name="Light Bun")
light_bun_material.diffuse_color = (0.8, 0.6, 0.4, 1)
dark_beef_material = bpy.data.materials.new(name="Dark Beef")
dark_beef_material.diffuse_color = (0.4, 0.2, 0.1, 1)
green_lettuce_material = bpy.data.materials.new(name="Green Lettuce")
green_lettuce_material.diffuse_color = (0.2, 0.8, 0.2, 1)
red_tomato_material = bpy.data.materials.new(name="Red Tomato")
red_tomato_material.diffuse_color = (0.8, 0.1, 0.1, 1)
yellow_cheese_material = bpy.data.materials.new(name="Yellow Cheese")
yellow_cheese_material.diffuse_color = (1, 0.8, 0.1, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the burger components
create_cylinder(1, 0.2, (0, 0, 0), "Bottom Bun", light_bun_material)
create_cylinder(0.9, 0.2, (0, 0, 0.2), "Beef Patty", dark_beef_material)
create_cylinder(1, 0.05, (0, 0, 0.35), "Lettuce", green_lettuce_material)
create_cylinder(0.9, 0.05, (0, 0, 0.4), "Tomato Slice 1", red_tomato_material)
create_cylinder(0.9, 0.05, (0, 0, 0.45), "Tomato Slice 2", red_tomato_material)

# Create cheese as a thin cube
bpy.ops.mesh.primitive_cube_add(size=1.8, location=(0, 0, 0.525))
cheese_slice = bpy.context.object
cheese_slice.scale[2] = 0.025
cheese_slice.name = "Cheese Slice"
cheese_slice.data.materials.append(yellow_cheese_material)

create_cylinder(1, 0.2, (0, 0, 0.65), "Top Bun", light_bun_material)


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
