# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_makes_a_model_of_coffee_mug" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that makes a model of coffee mug.

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a white material
white_color = bpy.data.materials.new(name="Mug White")
white_color.diffuse_color = (1, 1, 1, 1)  # White color definition

# Class to handle mug creation
class Mug:
    def __init__(self):
        self.body = None
        self.inner = None
        self.handle = None

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
        self.body = bpy.context.object
        self.body.name = "Mug Body"
        self.body.data.materials.append(white_color)

    def create_inner(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.4, location=(0, 0, 0.8))
        self.inner = bpy.context.object
        self.inner.name = "Mug Inner"

    def hollow_out(self):
        bool_mod = self.body.modifiers.new(type="BOOLEAN", name="Hollow Modifier")
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = self.inner
        bpy.context.view_layer.objects.active = self.body
        bpy.ops.object.modifier_apply(modifier="Hollow Modifier")
        bpy.data.objects.remove(self.inner)

    def create_handle(self):
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(1.5, 0, 0.75), major_radius=0.5, minor_radius=0.1, rotation=(math.pi/2, 0, 0))
        self.handle = bpy.context.object
        self.handle.name = "Handle"
        self.handle.data.materials.append(white_color)

    def attach_handle(self):
        bool_mod_handle = self.body.modifiers.new(type="BOOLEAN", name="Handle Attach Modifier")
        bool_mod_handle.operation = 'UNION'
        bool_mod_handle.object = self.handle
        bpy.context.view_layer.objects.active = self.body
        bpy.ops.object.modifier_apply(modifier="Handle Attach Modifier")
        bpy.data.objects.remove(self.handle)

# Create the mug
my_mug = Mug()
my_mug.create_body()
my_mug.create_inner()
my_mug.hollow_out()
my_mug.create_handle()
my_mug.attach_handle()


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
