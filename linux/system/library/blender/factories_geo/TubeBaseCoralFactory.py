# [FL_INDEX: keywords="blender_factory, procedural_3d, TubeBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TubeBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a tube coral structure. The object reveals the raw geometry of a tube coral — multiple thick, upright cylindrical tubes growing from a shared rounded base, each tube having a smooth surface and a slightly open hollow top. The tubes vary in height and angle slightly outward, creating a hand-like or bouquet arrangement. Without any texture or material color, the clean white geometry clearly shows the tubular form and the visible hollow openings at the top of each tube.

"""
Standalone Blender script – TubeBaseCoralFactory, seed 0.
Run:  blender --background --python TubeBaseCoralFactory.py

Pipeline (matches tube.py geo_coral_tube exactly):
  icosphere(2) → GeoNodes: SetPosition(perturb ±0.2) → DualMesh →
  6× (ExtrudeMesh + ScaleElements) → DeleteGeometry(top faces) →
  BEVEL(10%, 1seg) + SOLIDIFY(0.05) + SUBSURF(2) + DISPLACE(STUCCI, 0.1)
"""
import bpy
import numpy as np
import math

np.random.seed(0)

# ── Clean scene ───────────────────────────────────────────────────────────────
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)


def apply_geomod(obj, tree, name="GN"):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    gn = obj.modifiers.new(name, 'NODES')
    gn.node_group = tree
    bpy.ops.object.modifier_apply(modifier=name)


def make_geo_coral_tube():
    """Build GeoNodes tree replicating tube.py geo_coral_tube exactly.

    icosphere → perturb → DualMesh → 6× (ExtrudeMesh + ScaleElements) →
    DeleteGeometry(top faces)
    """
    # ── Parameters (match tube.py hardcoded constants) ──
    ico_sphere_perturb = 0.2
    growth_z = 1
    short_length_range = (0.2, 0.4)
    long_length_range = (0.4, 1.2)
    angles = np.linspace(np.pi * 2 / 5, np.pi / 10, 6)
    scales = np.linspace(1, 0.9, 6)
    face_perturb = 0.4
    growth_prob = 0.75
    seed = np.random.randint(1000)

    tree = bpy.data.node_groups.new("geo_coral_tube", 'GeometryNodeTree')
    for n in tree.nodes:
        tree.nodes.remove(n)

    inp = tree.nodes.new('NodeGroupInput');  inp.location = (-2400, 0)
    out = tree.nodes.new('NodeGroupOutput'); out.location = (6000, 0)
    tree.interface.new_socket('Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # ── SetPosition: perturb vertices ±0.2 ──
    rnd_perturb = tree.nodes.new('FunctionNodeRandomValue')
    rnd_perturb.location = (-2200, -200)
    rnd_perturb.data_type = 'FLOAT_VECTOR'
    rnd_perturb.inputs[0].default_value = (-ico_sphere_perturb,) * 3
    rnd_perturb.inputs[1].default_value = (ico_sphere_perturb,) * 3
    rnd_perturb.inputs[8].default_value = seed  # Seed

    set_pos = tree.nodes.new('GeometryNodeSetPosition')
    set_pos.location = (-2000, 0)
    tree.links.new(inp.outputs[0], set_pos.inputs['Geometry'])
    tree.links.new(rnd_perturb.outputs[0], set_pos.inputs['Offset'])

    # ── DualMesh: convert triangles to pentagons/hexagons ──
    dual = tree.nodes.new('GeometryNodeDualMesh')
    dual.location = (-1800, 0)
    tree.links.new(set_pos.outputs[0], dual.inputs[0])

    # ── InputNormal + SeparateXYZ (shared by all iterations) ──
    normal_node = tree.nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-1600, -600)

    sep_xyz = tree.nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-1400, -600)
    tree.links.new(normal_node.outputs[0], sep_xyz.inputs[0])

    # ── Initial "top" selection: upward-facing AND bernoulli(0.75) ──
    # Compare: normal.z > cos(angles[0])  i.e. within 72° of vertical
    cmp_init = tree.nodes.new('FunctionNodeCompare')
    cmp_init.location = (-1200, -600)
    cmp_init.data_type = 'FLOAT'
    cmp_init.operation = 'GREATER_THAN'
    tree.links.new(sep_xyz.outputs[2], cmp_init.inputs[0])  # Z
    cmp_init.inputs[1].default_value = float(np.cos(angles[0]))

    # Bernoulli: boolean random with probability = growth_prob
    bern = tree.nodes.new('FunctionNodeRandomValue')
    bern.location = (-1200, -800)
    bern.data_type = 'BOOLEAN'
    bern.inputs[6].default_value = growth_prob   # Probability
    bern.inputs[8].default_value = seed          # Seed

    # AND: direction_ok AND bernoulli
    and_node = tree.nodes.new('FunctionNodeBooleanMath')
    and_node.location = (-1000, -600)
    and_node.operation = 'AND'
    tree.links.new(cmp_init.outputs[0], and_node.inputs[0])
    tree.links.new(bern.outputs[3], and_node.inputs[1])  # Boolean at idx 3

    # Track current mesh output and top selection through iterations
    cur_mesh_out = dual.outputs[0]
    cur_top_out = and_node.outputs[0]

    # ── 6 extrusion iterations ──
    for i, (angle, scale) in enumerate(zip(angles, scales)):
        x = -800 + i * 1000
        y_off = 0

        # --- Direction = normalize(normal + (0,0,gz) + noise) ---

        # Random z growth: uniform(0, growth_z)
        rnd_gz = tree.nodes.new('FunctionNodeRandomValue')
        rnd_gz.location = (x, -300)
        rnd_gz.data_type = 'FLOAT'
        rnd_gz.inputs[2].default_value = 0.0
        rnd_gz.inputs[3].default_value = float(growth_z)
        rnd_gz.inputs[8].default_value = seed + i

        # CombineXYZ(0, 0, gz)
        comb_z = tree.nodes.new('ShaderNodeCombineXYZ')
        comb_z.location = (x, -500)
        comb_z.inputs[0].default_value = 0.0
        comb_z.inputs[1].default_value = 0.0
        tree.links.new(rnd_gz.outputs[1], comb_z.inputs[2])

        # normal + (0,0,gz)
        add_nz = tree.nodes.new('ShaderNodeVectorMath')
        add_nz.location = (x + 200, -400)
        add_nz.operation = 'ADD'
        tree.links.new(normal_node.outputs[0], add_nz.inputs[0])
        tree.links.new(comb_z.outputs[0], add_nz.inputs[1])

        # Face perturbation noise: uniform(-face_perturb, face_perturb)
        rnd_fp = tree.nodes.new('FunctionNodeRandomValue')
        rnd_fp.location = (x, -700)
        rnd_fp.data_type = 'FLOAT_VECTOR'
        rnd_fp.inputs[0].default_value = (-face_perturb,) * 3
        rnd_fp.inputs[1].default_value = (face_perturb,) * 3
        rnd_fp.inputs[8].default_value = seed + i

        # (normal + z_offset) + perturbation
        add_fp = tree.nodes.new('ShaderNodeVectorMath')
        add_fp.location = (x + 400, -400)
        add_fp.operation = 'ADD'
        tree.links.new(add_nz.outputs[0], add_fp.inputs[0])
        tree.links.new(rnd_fp.outputs[0], add_fp.inputs[1])

        # Normalize direction
        norm_dir = tree.nodes.new('ShaderNodeVectorMath')
        norm_dir.location = (x + 600, -400)
        norm_dir.operation = 'NORMALIZE'
        tree.links.new(add_fp.outputs[0], norm_dir.inputs[0])

        # --- Length: switch(upward → long, else → short) ---

        # Compare: normal.z > cos(angle) → upward check for current iteration
        cmp_dir = tree.nodes.new('FunctionNodeCompare')
        cmp_dir.location = (x, -900)
        cmp_dir.data_type = 'FLOAT'
        cmp_dir.operation = 'GREATER_THAN'
        tree.links.new(sep_xyz.outputs[2], cmp_dir.inputs[0])
        cmp_dir.inputs[1].default_value = float(np.cos(angle))

        # Long length: uniform(0.4, 1.2)
        rnd_long = tree.nodes.new('FunctionNodeRandomValue')
        rnd_long.location = (x + 200, -1000)
        rnd_long.data_type = 'FLOAT'
        rnd_long.inputs[2].default_value = float(long_length_range[0])
        rnd_long.inputs[3].default_value = float(long_length_range[1])
        rnd_long.inputs[8].default_value = seed + i

        # Short length: uniform(0.2, 0.4)
        rnd_short = tree.nodes.new('FunctionNodeRandomValue')
        rnd_short.location = (x + 200, -1200)
        rnd_short.data_type = 'FLOAT'
        rnd_short.inputs[2].default_value = float(short_length_range[0])
        rnd_short.inputs[3].default_value = float(short_length_range[1])
        rnd_short.inputs[8].default_value = seed + i

        # Switch: upward=True → long (True), upward=False → short (False)
        switch = tree.nodes.new('GeometryNodeSwitch')
        switch.location = (x + 400, -1000)
        switch.input_type = 'FLOAT'
        tree.links.new(cmp_dir.outputs[0], switch.inputs[0])      # Switch
        tree.links.new(rnd_short.outputs[1], switch.inputs[1])     # False → short
        tree.links.new(rnd_long.outputs[1], switch.inputs[2])      # True → long

        # --- ExtrudeMesh ---
        extrude = tree.nodes.new('GeometryNodeExtrudeMesh')
        extrude.location = (x + 600, y_off)
        tree.links.new(cur_mesh_out, extrude.inputs[0])         # Mesh
        tree.links.new(cur_top_out, extrude.inputs[1])           # Selection
        tree.links.new(norm_dir.outputs[0], extrude.inputs[2])  # Offset
        tree.links.new(switch.outputs[0], extrude.inputs[3])    # Offset Scale

        # --- ScaleElements ---
        scale_elem = tree.nodes.new('GeometryNodeScaleElements')
        scale_elem.location = (x + 800, y_off)
        tree.links.new(extrude.outputs[0], scale_elem.inputs[0])  # Geometry
        tree.links.new(extrude.outputs[1], scale_elem.inputs[1])  # Selection = Top
        scale_elem.inputs[2].default_value = float(scale)         # Scale

        # Update tracked outputs for next iteration
        cur_mesh_out = scale_elem.outputs[0]
        cur_top_out = extrude.outputs[1]  # Top

    # ── Delete top faces (open tube ends) ──
    delete = tree.nodes.new('GeometryNodeDeleteGeometry')
    delete.location = (5600, 0)
    delete.domain = 'FACE'
    tree.links.new(cur_mesh_out, delete.inputs[0])
    tree.links.new(cur_top_out, delete.inputs[1])

    tree.links.new(delete.outputs[0], out.inputs[0])
    return tree


# ══════════════════════════════════════════════════════════════════════════════
# Main: create icosphere, apply GeoNodes, apply modifiers
# ══════════════════════════════════════════════════════════════════════════════

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
obj = bpy.context.active_object
obj.name = "TubeBaseCoralFactory"

# Apply GeoNodes tube extrusion
apply_geomod(obj, make_geo_coral_tube(), "CoralTube")
print(f"After GeoNodes: verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# Post-modifiers (match tube.py create_asset)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# BEVEL: offset_type=PERCENT, width_pct=10, segments=1
m_bev = obj.modifiers.new("Bevel", "BEVEL")
m_bev.offset_type = 'PERCENT'
m_bev.width_pct = 10
m_bev.segments = 1
bpy.ops.object.modifier_apply(modifier="Bevel")

# SOLIDIFY: thickness=0.05
m_sol = obj.modifiers.new("Solidify", "SOLIDIFY")
m_sol.thickness = 0.05
bpy.ops.object.modifier_apply(modifier="Solidify")

# SUBSURF: levels=2
m_sub = obj.modifiers.new("SubSurf", "SUBSURF")
m_sub.levels = 2
m_sub.render_levels = 2
bpy.ops.object.modifier_apply(modifier="SubSurf")

# DISPLACE: STUCCI texture, strength=0.1, mid_level=0
tex = bpy.data.textures.new("tube_coral", type='STUCCI')
m_disp = obj.modifiers.new("Displace", "DISPLACE")
m_disp.texture = tex
m_disp.strength = 0.1
m_disp.mid_level = 0
bpy.ops.object.modifier_apply(modifier="Displace")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
obj.name = "TubeBaseCoralFactory"
print(f"Done: TubeBaseCoralFactory  verts={len(obj.data.vertices)}  "
      f"faces={len(obj.data.polygons)}")
