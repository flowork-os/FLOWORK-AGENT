# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_python_code__make_cat_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender python code, make cat bed.

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the bed
bed_material = bpy.data.materials.new(name="BedMaterial")
bed_material.diffuse_color = (0.5, 0.35, 0.25, 1)  # A warm brown shade

# Function to create a cylinder
def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(bed_material)
    return obj

# Step 1: Create the bed base
base_cylinder = create_cylinder(1.5, 0.1, (0, 0, 0), "BedBase")

# Step 2: Create the raised edges using a torus
bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.2, location=(0, 0, 0.15))
raised_edges = bpy.context.object
raised_edges.name = "RaisedEdges"
raised_edges.data.materials.append(bed_material)

# Step 3: Create the indentation for the cat
cat_indent = create_cylinder(1.3, 0.1, (0, 0, 0.05), "CatIndentation")

# Step 4: Apply boolean modifier to create the hollow part
bpy.context.view_layer.objects.active = base_cylinder
bool_modifier = base_cylinder.modifiers.new(type="BOOLEAN", name="Cutout")
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = cat_indent
bpy.ops.object.modifier_apply(modifier="Cutout")

# Clean up by removing the indentation object
bpy.data.objects.remove(cat_indent, do_unlink=True)


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
