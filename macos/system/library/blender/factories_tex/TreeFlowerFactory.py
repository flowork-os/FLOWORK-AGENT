# [FL_INDEX: keywords="blender_factory, procedural_3d, TreeFlowerFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TreeFlowerFactory | Category: factories_tex
# Prompt: A 3D model of a single large flower rendered from a top-down perspective. The flower features numerous flat, elongated white petals radiating outward from a raised, dome-shaped central disk filled with densely packed small cylindrical florets in a warm tan hue.

"""TreeFlowerFactory standalone script with materials.

Geometry copied verbatim from objects_blender/trees/TreeFlowerFactory.py.
  - shader_petal: Principled + Translucent mix with random tree_petal_hsv color
  - shader_flower_center: AmbientOcclusion -> ColorRamp -> Principled

Natural asset -- NO wear_tear. Seed SEED."""


import colorsys
import math
import os
import random

import bmesh
import bpy
import numpy as np

# Material helpers

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1,
                                  max(0, min(1, float(s))),
                                  max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _tree_petal_hsv():
    """

    40% pink, 20% white, 20% red, 20% yellow."""

    r = np.random.uniform(0, 1)
    if r < 0.4:
        # plant_pink: wrap_gaussian(0.88, 0.06), N(0.6, 0.05), N(0.8, 0.05)
        h = float(np.random.normal(0.88, 0.06)) % 1.0
        s = float(np.clip(np.random.normal(0.6, 0.05), 0, 1))
        v = float(np.clip(np.random.normal(0.8, 0.05), 0, 1))
    elif r < 0.6:
        # plant_white: wrap_gaussian(0.0, 0.06), U(0.0, 0.2), N(0.95, 0.02)
        h = float(np.random.normal(0.0, 0.06)) % 1.0
        s = float(np.random.uniform(0.0, 0.2))
        v = float(np.clip(np.random.normal(0.95, 0.02), 0, 1))
    elif r < 0.8:
        # plant_red: wrap_gaussian(0.0, 0.05), N(0.9, 0.03), N(0.6, 0.05)
        h = float(np.random.normal(0.0, 0.05)) % 1.0
        s = float(np.clip(np.random.normal(0.9, 0.03), 0, 1))
        v = float(np.clip(np.random.normal(0.6, 0.05), 0, 1))
    else:
        # plant_yellow: wrap_gaussian(0.15, 0.005), N(0.95, 0.02), N(0.9, 0.02)
        h = float(np.random.normal(0.15, 0.005)) % 1.0
        s = float(np.clip(np.random.normal(0.95, 0.02), 0, 1))
        v = float(np.clip(np.random.normal(0.9, 0.02), 0, 1))
    return (h, s, v)

def create_petal_material(color_hsv, name="PetalMaterial"):
    """shader_petal: Principled + Translucent mix, random petal color."""


    petal_rgba = _hsv2rgba(*color_hsv)

    # Consume numpy.random in same order as shader_petal
    translucent_color_change = float(np.random.uniform(0.1, 0.6))  # consumed (unused in shader, mirror RNG)
    specular = float(np.clip(np.random.normal(0.6, 0.1), 0, 1))
    roughness = float(np.clip(np.random.normal(0.4, 0.05), 0, 1))
    translucent_amt = float(np.clip(np.random.normal(0.3, 0.05), 0, 1))

    mat = _new_mat(name)
    nt = mat.node_tree
    N, L = nt.nodes, nt.links

    out = N.new('ShaderNodeOutputMaterial')

    petal_col = N.new('ShaderNodeRGB')
    petal_col.outputs[0].default_value = petal_rgba

    trans = N.new('ShaderNodeBsdfTranslucent')
    L.new(petal_col.outputs[0], trans.inputs['Color'])

    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(petal_col.outputs[0], bsdf.inputs['Base Color'])
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = specular
    bsdf.inputs['Roughness'].default_value = roughness

    mix_sh = N.new('ShaderNodeMixShader')
    mix_sh.inputs['Fac'].default_value = translucent_amt
    L.new(bsdf.outputs[0], mix_sh.inputs[1])
    L.new(trans.outputs[0], mix_sh.inputs[2])

    L.new(mix_sh.outputs[0], out.inputs['Surface'])
    return mat

def create_flower_center_material(name="FlowerCenterMaterial"):
    """shader_flower_center: AmbientOcclusion -> ColorRamp (dark -> bright tips)."""


    mat = _new_mat(name)
    nt = mat.node_tree
    N, L = nt.nodes, nt.links

    out = N.new('ShaderNodeOutputMaterial')

    ao = N.new('ShaderNodeAmbientOcclusion')

    cr = N.new('ShaderNodeValToRGB')
    cr.color_ramp.elements.new(1)
    cr.color_ramp.elements[0].position = 0.4841
    cr.color_ramp.elements[0].color = (0.0127, 0.0075, 0.0026, 1.0)
    cr.color_ramp.elements[1].position = 0.8591
    cr.color_ramp.elements[1].color = (0.0848, 0.0066, 0.0007, 1.0)
    cr.color_ramp.elements[2].position = 1.0
    cr.color_ramp.elements[2].color = (1.0, 0.6228, 0.1069, 1.0)
    L.new(ao.outputs['Color'], cr.inputs['Fac'])

    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(cr.outputs['Color'], bsdf.inputs['Base Color'])
    L.new(bsdf.outputs[0], out.inputs[0])

    return mat


SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

# Mirror TreeFlowerFactory.__init__ RNG consumption order:
#   1) colors.tree_petal_hsv()  -> petal_color_hsv
#   2) shader_petal samples (specular, roughness, translucent_amt)
#   3) shader_flower_center (no RNG)
#   4) get_flower_params(rad)  -- but rad itself was sampled outside FixedSeed,
#      and species params are re-sampled inside build() via sample_params() anyway.
PETAL_COLOR_HSV = _tree_petal_hsv()
MAT_PETAL = create_petal_material(PETAL_COLOR_HSV, name="Petal")
MAT_FLOWER_CENTER = create_flower_center_material(name="FlowerCenter")

# No wear_tear for natural assets.

# Original geometry (copied verbatim from objects_blender/trees/TreeFlowerFactory.py)

random.seed(SEED)
np.random.seed(SEED)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    valid = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not valid:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active = valid[0]
    if len(valid) > 1:
        bpy.ops.object.join()
    return bpy.context.active_object

def make_center_protrusions(center_rad, seed_size, n_rings=6, n_sides=6):
    """Create club-shaped seed protrusions on the flower center disc."""

    min_dist = seed_size * 1.5
    positions = []
    max_seeds = 55
    for _ in range(3000):
        angle = np.random.uniform(0, 2 * math.pi)
        r = np.random.uniform(0, center_rad * 0.90)
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        if all(math.sqrt((x - px) ** 2 + (y - py) ** 2) >= min_dist
               for px, py in positions):
            positions.append((x, y))
            if len(positions) >= max_seeds:
                break

    bm = bmesh.new()

    def _radius(t, base_r):
        if t <= 0.0:
            return 0.0
        elif t <= 0.316:
            f = t / 0.316
            return base_r * 0.447 * f ** 0.7 * 3.0
        else:
            f = (t - 0.316) / 0.684
            val = 0.016 + (0.447 - 0.016) * (1 - f) ** 1.5
            return base_r * val * 3.0

    disc_z = center_rad * 0.03

    for px, py in positions:
        h_scale = np.random.uniform(0.40, 1.15)
        length = seed_size * 10 * h_scale

        dist_c = math.sqrt(px ** 2 + py ** 2) + 1e-9
        lean = np.random.uniform(0.0, 0.18) * (dist_c / center_rad)
        lean_dx = (px / dist_c) * lean
        lean_dy = (py / dist_c) * lean

        ring_verts_list = []
        for ri in range(n_rings):
            t = ri / max(n_rings - 1, 1)
            r = _radius(t, seed_size)
            z = disc_z + length * t
            cx = px + lean_dx * length * t
            cy = py + lean_dy * length * t

            verts = []
            for si in range(n_sides):
                a = 2 * math.pi * si / n_sides
                verts.append(bm.verts.new((cx + r * math.cos(a),
                                           cy + r * math.sin(a), z)))
            ring_verts_list.append(verts)

        for ri in range(n_rings - 1):
            for si in range(n_sides):
                sn = (si + 1) % n_sides
                try:
                    bm.faces.new([ring_verts_list[ri][si], ring_verts_list[ri][sn],
                                  ring_verts_list[ri + 1][sn], ring_verts_list[ri + 1][si]])
                except ValueError:
                    pass

        tip_z = disc_z + length
        tip_cx = px + lean_dx * length
        tip_cy = py + lean_dy * length
        tip = bm.verts.new((tip_cx, tip_cy, tip_z))
        for si in range(n_sides):
            sn = (si + 1) % n_sides
            try:
                bm.faces.new([ring_verts_list[-1][si], ring_verts_list[-1][sn], tip])
            except ValueError:
                pass

    mesh = bpy.data.meshes.new("CenterSeeds")
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    obj = bpy.data.objects.new("CenterSeeds", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def _build_follow_curve_ng():
    if 'follow_curve' in bpy.data.node_groups:
        return bpy.data.node_groups['follow_curve']
    ng = bpy.data.node_groups.new("follow_curve", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Curve', in_out='INPUT', socket_type='NodeSocketGeometry')
    s = ng.interface.new_socket('Curve Min', in_out='INPUT', socket_type='NodeSocketFloat'); s.default_value = 0.0
    s = ng.interface.new_socket('Curve Max', in_out='INPUT', socket_type='NodeSocketFloat'); s.default_value = 1.0
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    pos = N.new('GeometryNodeInputPosition')
    cap = N.new('GeometryNodeCaptureAttribute')
    cap.capture_items.new('VECTOR', 'Position')
    L.new(gi.outputs['Geometry'], cap.inputs['Geometry'])
    L.new(pos.outputs['Position'], cap.inputs['Position'])
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(cap.outputs['Position'], sep.inputs['Vector'])
    stat = N.new('GeometryNodeAttributeStatistic'); stat.data_type = 'FLOAT'
    L.new(cap.outputs['Geometry'], stat.inputs['Geometry'])
    L.new(sep.outputs['Z'], stat.inputs['Attribute'])
    mr = N.new('ShaderNodeMapRange')
    L.new(sep.outputs['Z'], mr.inputs['Value'])
    L.new(stat.outputs['Min'], mr.inputs[1]); L.new(stat.outputs['Max'], mr.inputs[2])
    L.new(gi.outputs['Curve Min'], mr.inputs[3]); L.new(gi.outputs['Curve Max'], mr.inputs[4])
    cl = N.new('GeometryNodeCurveLength'); L.new(gi.outputs['Curve'], cl.inputs['Curve'])
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L.new(mr.outputs['Result'], mul.inputs[0]); L.new(cl.outputs['Length'], mul.inputs[1])
    sc = N.new('GeometryNodeSampleCurve'); sc.mode = 'LENGTH'
    L.new(gi.outputs['Curve'], sc.inputs['Curves']); L.new(mul.outputs[0], sc.inputs['Length'])
    cross = N.new('ShaderNodeVectorMath'); cross.operation = 'CROSS_PRODUCT'
    L.new(sc.outputs['Tangent'], cross.inputs[0]); L.new(sc.outputs['Normal'], cross.inputs[1])
    sx = N.new('ShaderNodeVectorMath'); sx.operation = 'SCALE'
    L.new(cross.outputs['Vector'], sx.inputs[0]); L.new(sep.outputs['X'], sx.inputs['Scale'])
    sy = N.new('ShaderNodeVectorMath'); sy.operation = 'SCALE'
    L.new(sc.outputs['Normal'], sy.inputs[0]); L.new(sep.outputs['Y'], sy.inputs['Scale'])
    add = N.new('ShaderNodeVectorMath')
    L.new(sx.outputs['Vector'], add.inputs[0]); L.new(sy.outputs['Vector'], add.inputs[1])
    sp = N.new('GeometryNodeSetPosition')
    L.new(cap.outputs['Geometry'], sp.inputs['Geometry'])
    L.new(sc.outputs['Position'], sp.inputs['Position']); L.new(add.outputs['Vector'], sp.inputs['Offset'])
    L.new(sp.outputs['Geometry'], go.inputs['Geometry'])
    return ng

def _build_petal_ng(length, base_width, upper_width, curl, wrinkle,
                    bevel=6.8, point=1.0, point_height=0.5, res_h=8, res_v=4):
    ng = bpy.data.node_groups.new("flower_petal", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    grid = N.new('GeometryNodeMeshGrid')
    grid.inputs['Size X'].default_value = 1.0; grid.inputs['Size Y'].default_value = 1.0
    grid.inputs['Vertices X'].default_value = res_v
    grid.inputs['Vertices Y'].default_value = res_h * 2 + 1
    pos = N.new('GeometryNodeInputPosition')
    cap = N.new('GeometryNodeCaptureAttribute')
    cap.capture_items.new('VECTOR', 'OrigPos')
    L.new(grid.outputs['Mesh'], cap.inputs['Geometry']); L.new(pos.outputs['Position'], cap.inputs['OrigPos'])
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(cap.outputs['OrigPos'], sep.inputs['Vector'])
    add1 = N.new('ShaderNodeMath'); L.new(sep.outputs['X'], add1.inputs[0]); add1.inputs[1].default_value = 0.5
    absy = N.new('ShaderNodeMath'); absy.operation = 'ABSOLUTE'; L.new(sep.outputs['Y'], absy.inputs[0])
    m2 = N.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; L.new(absy.outputs[0], m2.inputs[0]); m2.inputs[1].default_value = 2.0
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; L.new(m2.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = bevel
    bev = N.new('ShaderNodeMath'); bev.operation = 'MULTIPLY_ADD'
    L.new(pw.outputs[0], bev.inputs[0]); bev.inputs[1].default_value = -1.0; bev.inputs[2].default_value = 1.0
    mxu = N.new('ShaderNodeMath'); mxu.operation = 'MULTIPLY'; L.new(add1.outputs[0], mxu.inputs[0]); L.new(bev.outputs[0], mxu.inputs[1])
    wid = N.new('ShaderNodeMath'); wid.operation = 'MULTIPLY_ADD'
    L.new(mxu.outputs[0], wid.inputs[0]); wid.inputs[1].default_value = upper_width; wid.inputs[2].default_value = base_width
    ny = N.new('ShaderNodeMath'); ny.operation = 'MULTIPLY'; L.new(sep.outputs['Y'], ny.inputs[0]); L.new(wid.outputs[0], ny.inputs[1])
    pwp = N.new('ShaderNodeMath'); pwp.operation = 'POWER'; L.new(absy.outputs[0], pwp.inputs[0]); pwp.inputs[1].default_value = point
    pti = N.new('ShaderNodeMath'); pti.operation = 'MULTIPLY_ADD'
    L.new(pwp.outputs[0], pti.inputs[0]); pti.inputs[1].default_value = -1.0; pti.inputs[2].default_value = 1.0
    pts = N.new('ShaderNodeMath'); pts.operation = 'MULTIPLY'; L.new(pti.outputs[0], pts.inputs[0]); pts.inputs[1].default_value = point_height
    ptb = N.new('ShaderNodeMath'); ptb.operation = 'MULTIPLY_ADD'
    ptb.inputs[0].default_value = point_height; ptb.inputs[1].default_value = -1.0; ptb.inputs[2].default_value = 1.0
    pta = N.new('ShaderNodeMath'); L.new(pts.outputs[0], pta.inputs[0]); L.new(ptb.outputs[0], pta.inputs[1])
    mz1 = N.new('ShaderNodeMath'); mz1.operation = 'MULTIPLY'; L.new(pta.outputs[0], mz1.inputs[0]); L.new(bev.outputs[0], mz1.inputs[1])
    nz = N.new('ShaderNodeMath'); nz.operation = 'MULTIPLY'; L.new(add1.outputs[0], nz.inputs[0]); L.new(mz1.outputs[0], nz.inputs[1])
    sep2 = N.new('ShaderNodeSeparateXYZ'); L.new(cap.outputs['OrigPos'], sep2.inputs['Vector'])
    mnx = N.new('ShaderNodeMath'); mnx.operation = 'MULTIPLY'; L.new(sep2.outputs['X'], mnx.inputs[0]); mnx.inputs[1].default_value = 0.05
    cn = N.new('ShaderNodeCombineXYZ'); L.new(mnx.outputs[0], cn.inputs['X']); L.new(sep2.outputs['Y'], cn.inputs['Y'])
    noise = N.new('ShaderNodeTexNoise'); noise.noise_dimensions = '2D'
    noise.inputs['Scale'].default_value = 7.9; noise.inputs['Detail'].default_value = 0.0; noise.inputs['Distortion'].default_value = 0.2
    L.new(cn.outputs['Vector'], noise.inputs['Vector'])
    sn = N.new('ShaderNodeMath'); L.new(noise.outputs[0], sn.inputs[0]); sn.inputs[1].default_value = -0.5
    wrk = N.new('ShaderNodeMath'); wrk.operation = 'MULTIPLY'; L.new(sn.outputs[0], wrk.inputs[0]); wrk.inputs[1].default_value = wrinkle
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(wrk.outputs[0], comb.inputs['X']); L.new(ny.outputs[0], comb.inputs['Y']); L.new(nz.outputs[0], comb.inputs['Z'])
    sp = N.new('GeometryNodeSetPosition')
    L.new(cap.outputs['Geometry'], sp.inputs['Geometry']); L.new(comb.outputs['Vector'], sp.inputs['Position'])
    mid_y = length / 2; end_y = mid_y * (1 + math.cos(curl)); end_z = mid_y * math.sin(curl)
    bez = N.new('GeometryNodeCurveQuadraticBezier'); bez.inputs['Resolution'].default_value = 16
    bez.inputs['Start'].default_value = (0, 0, 0)
    bez.inputs['Middle'].default_value = (0, mid_y, 0)
    bez.inputs['End'].default_value = (0, end_y, end_z)
    fc_ng = _build_follow_curve_ng()
    fc = N.new('GeometryNodeGroup'); fc.node_tree = fc_ng
    L.new(sp.outputs['Geometry'], fc.inputs['Geometry']); L.new(bez.outputs['Curve'], fc.inputs['Curve'])
    fc.inputs['Curve Min'].default_value = 0.0; fc.inputs['Curve Max'].default_value = 1.0
    L.new(fc.outputs['Geometry'], go.inputs['Geometry'])
    return ng

def make_petal_mesh(length, base_width, upper_width, curl=0.0, wrinkle=0.005,
                    bevel=6.8, point=1.0, point_height=0.5, res_h=8, res_v=4):
    petal_ng = _build_petal_ng(length, base_width, upper_width, curl, wrinkle,
                               bevel, point, point_height, res_h, res_v)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object
    mod = obj.modifiers.new("Petal", 'NODES')
    mod.node_group = petal_ng
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.node_groups.remove(petal_ng)
    return obj

def make_flower(seed=0):
    np.random.seed(seed)
    random.seed(seed)

    overall_rad = np.random.uniform(0.15, 0.25)
    pct_inner = np.random.uniform(0.05, 0.4)
    center_rad = overall_rad * pct_inner
    petal_length = overall_rad * (1 - pct_inner)

    n_petal_width_denom = max(5, np.random.normal(20, 5))
    base_width = 2 * math.pi * overall_rad * pct_inner / n_petal_width_denom
    top_width = overall_rad * np.clip(np.random.normal(0.7, 0.3), base_width * 1.2, 100)

    circumference = 2 * math.pi * center_rad
    n_petals = max(5, int(circumference / max(base_width, 0.001) * 1.2))
    n_petals = min(n_petals, 30)

    petal_max_width = top_width
    seed_size = np.random.uniform(0.005, 0.01)
    wrinkle = np.random.uniform(0.003, 0.02)
    curl = np.radians(np.random.normal(30, 50))

    angles = np.sort(np.random.uniform(-20, 100, 2))
    min_petal_angle = np.radians(angles[0])
    max_petal_angle = np.radians(angles[1])

    inst_rad = overall_rad * np.random.normal(1, 0.05)
    inst_pct = np.random.uniform(0.05, 0.4)
    inst_angles = np.sort(np.random.uniform(-20, 100, 2))
    inst_curl = np.radians(np.random.normal(30, 50))
    pct_inner = pct_inner * 0.75 + inst_pct * 0.25
    center_rad = overall_rad * pct_inner
    petal_length = overall_rad * (1 - pct_inner)
    min_petal_angle = min_petal_angle * 0.75 + np.radians(inst_angles[0]) * 0.25
    max_petal_angle = max_petal_angle * 0.75 + np.radians(inst_angles[1]) * 0.25
    curl = curl * 0.75 + inst_curl * 0.25

    parts = []

    # 1. Center disc (flower_center material)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=12, ring_count=8, radius=center_rad, location=(0, 0, 0)
    )
    center = bpy.context.active_object
    center.scale = (1.0, 1.0, 0.05)
    apply_tf(center)
    center.data.materials.append(MAT_FLOWER_CENTER)
    parts.append(center)

    # 2. Club-shaped seed protrusions (flower_center material)
    seed_protrusions = make_center_protrusions(center_rad, seed_size)
    seed_protrusions.data.materials.append(MAT_FLOWER_CENTER)
    parts.append(seed_protrusions)

    # 3. Petals -- Fibonacci spiral (petal material)
    GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))
    for i in range(n_petals):
        yaw = i * GOLDEN_ANGLE
        pitch = np.random.uniform(min_petal_angle, max_petal_angle)

        petal = make_petal_mesh(
            length=petal_length,
            base_width=base_width,
            upper_width=top_width,
            curl=curl * np.random.uniform(0.7, 1.3),
            wrinkle=wrinkle,
            res_h=8, res_v=8,
        )

        bpy.context.view_layer.objects.active = petal
        petal.select_set(True)
        sol = petal.modifiers.new("sol", "SOLIDIFY")
        sol.thickness = 0.003
        sol.offset = 0
        bpy.ops.object.modifier_apply(modifier=sol.name)

        petal.rotation_euler = (pitch, 0, yaw - math.pi / 2)
        px = center_rad * math.cos(yaw)
        py = center_rad * math.sin(yaw)
        petal.location = (px, py, 0)
        apply_tf(petal)

        bm = bmesh.new()
        bm.from_mesh(petal.data)
        for v in bm.verts:
            noise = math.sin(v.co.x * 5.73 + v.co.y * 7.41 + i * 3.1) * 0.5
            v.co.z += noise * wrinkle * 0.5
        bm.to_mesh(petal.data)
        bm.free()

        petal.data.materials.append(MAT_PETAL)
        parts.append(petal)

    result = join_objs(parts)
    result.name = "TreeFlowerFactory"

    bpy.ops.object.select_all(action="DESELECT")
    result.select_set(True)
    bpy.context.view_layer.objects.active = result
    bpy.ops.object.shade_flat()
    for i in range(len(result.data.materials)):
        if result.data.materials[i] is None:
            result.data.materials[i] = MAT_PETAL

    return result

clear_scene()
result = make_flower(SEED)
n_verts = len(result.data.vertices)
n_faces = len(result.data.polygons)
dims = result.dimensions

