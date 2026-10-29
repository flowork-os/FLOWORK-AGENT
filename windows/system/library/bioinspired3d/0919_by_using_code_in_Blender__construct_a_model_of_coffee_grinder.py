# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender__construct_a_model_of_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender, construct a model of coffee grinder.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Grinder:
    def __init__(self):
        self.create_materials()
        self.create_body()
        self.create_compartment()
        self.create_handle()
        self.create_knob()

    def create_materials(self):
        self.metal = bpy.data.materials.new(name='Metal')
        self.metal.diffuse_color = (0.5, 0.5, 0.5, 1)
        self.wood = bpy.data.materials.new(name='Wood')
        self.wood.diffuse_color = (0.55, 0.27, 0.07, 1)

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
        body = bpy.context.object
        body.name = 'Grinder Body'
        body.data.materials.append(self.metal)

    def create_compartment(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.8, location=(0, 0, 2.1))
        compartment = bpy.context.object
        compartment.name = 'Bean Compartment'
        compartment.data.materials.append(self.wood)

    def create_handle(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(0, 1.1, 1.5), rotation=(1.57, 0, 0))
        handle = bpy.context.object
        handle.name = 'Handle'
        handle.data.materials.append(self.metal)

    def create_knob(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 1.5, 1.5))
        knob = bpy.context.object
        knob.name = 'Handle Knob'
        knob.data.materials.append(self.wood)

# Instantiate the Grinder
Grinder()


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
