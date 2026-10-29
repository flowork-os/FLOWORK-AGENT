# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

from __future__ import annotations

import cadquery as cq
import math

# ===== shim core =====
def _rpy_R(r, p, y):
    """Rotation matrix Rz(yaw)@Ry(pitch)@Rx(roll) as rows (URDF convention)."""
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )

def _mat_mul(A, B):
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )

def _mat_vec(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))

class _Tf:
    """Rigid transform: rotation matrix R (rows) + translation t."""
    __slots__ = ("R", "t")
    _I = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    def __init__(self, R=None, t=(0.0, 0.0, 0.0)):
        self.R = R if R is not None else _Tf._I
        self.t = (float(t[0]), float(t[1]), float(t[2]))

    @staticmethod
    def from_origin(origin):
        if origin is None:
            return _Tf()
        xyz = getattr(origin, "xyz", (0.0, 0.0, 0.0))
        rpy = getattr(origin, "rpy", (0.0, 0.0, 0.0))
        return _Tf(_rpy_R(rpy[0], rpy[1], rpy[2]), xyz)

    def __matmul__(self, o):
        return _Tf(_mat_mul(self.R, o.R),
                   tuple(a + b for a, b in zip(_mat_vec(self.R, o.t), self.t)))

    def location(self):
        R, t = self.R, self.t
        xdir = cq.Vector(R[0][0], R[1][0], R[2][0])
        zdir = cq.Vector(R[0][2], R[1][2], R[2][2])
        return cq.Location(cq.Plane(origin=cq.Vector(*t), xDir=xdir, normal=zdir))

class ValidationError(ValueError):
    pass

class ArticulationType:
    REVOLUTE = "revolute"
    CONTINUOUS = "continuous"
    PRISMATIC = "prismatic"
    FIXED = "fixed"
    FLOATING = "floating"

class Origin:
    __slots__ = ("xyz", "rpy")

    def __init__(self, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)):
        self.xyz = (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        self.rpy = (float(rpy[0]), float(rpy[1]), float(rpy[2]))

class Material:
    def __init__(self, name, rgba=None, texture=None, *, color=None):
        self.name = str(name)
        c = rgba if rgba is not None else color
        if c is not None:
            c = tuple(float(v) for v in c)
            if len(c) == 3:
                c = c + (1.0,)
        self.rgba = c
        self.texture = texture

class MotionLimits:
    def __init__(self, effort=1.0, velocity=1.0, lower=None, upper=None):
        self.effort = float(effort)
        self.velocity = float(velocity)
        self.lower = None if lower is None else float(lower)
        self.upper = None if upper is None else float(upper)

class Box:
    __slots__ = ("size",)

    def __init__(self, size):
        self.size = (float(size[0]), float(size[1]), float(size[2]))

    def _cq(self):
        sx, sy, sz = self.size
        return cq.Solid.makeBox(sx, sy, sz, cq.Vector(-sx / 2, -sy / 2, -sz / 2))

class Cylinder:
    __slots__ = ("radius", "length")

    def __init__(self, radius, length=None, *, height=None):
        self.radius = float(radius)
        self.length = float(height if length is None else length)

    @property
    def height(self):
        return self.length

    def _cq(self):
        return cq.Solid.makeCylinder(
            self.radius, self.length, cq.Vector(0, 0, -self.length / 2), cq.Vector(0, 0, 1)
        )

def _to_shape(model):
    """Coerce a cadquery object (Workplane/Shape/Assembly) or a shim geometry
    wrapper into a single cq.Shape."""
    if isinstance(model, _CQMesh):
        return model.shape
    if hasattr(model, "_cq"):
        return model._cq()
    if isinstance(model, cq.Assembly):
        return model.toCompound()
    if isinstance(model, cq.Workplane):
        vals = [v for v in model.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValidationError("cadquery Workplane has no shape values")
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(model, cq.Shape):
        return model
    raise ValidationError("unsupported cadquery model type: %r" % type(model))

class _CQMesh:
    """Mesh stand-in that simply carries an exact cadquery B-rep shape."""
    __slots__ = ("shape", "name")

    def __init__(self, shape, name=None):
        self.shape = shape
        self.name = name

    def _cq(self):
        return self.shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_to_shape(model), name=name if isinstance(name, str) else None)

class Visual:
    __slots__ = ("geometry", "origin", "material", "name")

    def __init__(self, geometry, origin=None, material=None, name=None):
        self.geometry = geometry
        self.origin = origin or Origin()
        self.material = material
        self.name = name

class Part:
    def __init__(self, name, visuals=None, inertial=None, meta=None):
        self.name = name
        self.visuals = list(visuals or [])
        self.collisions = []
        self.inertial = inertial
        self.meta = dict(meta or {})

    def visual(self, geometry, *, origin=None, material=None, color=None, name=None):
        if color is not None and material is None:
            material = color if isinstance(color, (str, Material)) else Material("inline", rgba=color)
        v = Visual(geometry, origin=origin, material=material, name=name)
        self.visuals.append(v)
        return v

    def get_visual(self, name):
        for v in self.visuals:
            if v.name == name:
                return v
        raise ValidationError("unknown visual %r" % name)

class Articulation:
    def __init__(self, name, articulation_type, parent, child, origin=None,
                 axis=(0.0, 0.0, 1.0), motion_limits=None, motion_properties=None,
                 mimic=None, meta=None):
        self.name = name
        self.articulation_type = articulation_type
        self.parent = parent if isinstance(parent, str) else parent.name
        self.child = child if isinstance(child, str) else child.name
        self.origin = origin or Origin()
        self.axis = tuple(float(a) for a in axis)
        self.motion_limits = motion_limits
        self.motion_properties = motion_properties
        self.mimic = mimic
        self.meta = dict(meta or {})

    # aliases used by some scripts
    @property
    def joint_type(self):
        return self.articulation_type

    @property
    def limit(self):
        return self.motion_limits

class ArticulatedObject:
    def __init__(self, name, parts=None, articulations=None, materials=None, meta=None, assets=None):
        self.name = name
        self.parts = list(parts or [])
        self.articulations = list(articulations or [])
        self.materials = list(materials or [])
        self.meta = dict(meta or {})
        self.assets = assets

    # ---- builders ----
    def part(self, name, *, visuals=None, inertial=None, meta=None):
        p = Part(name, visuals=visuals, inertial=inertial, meta=meta)
        self.parts.append(p)
        return p

    link = part

    def articulation(self, name, articulation_type, parent, child, *, origin=None,
                     axis=None, motion_limits=None, motion_properties=None, mimic=None, meta=None):
        a = Articulation(name, articulation_type, parent, child, origin=origin,
                         axis=axis or (0.0, 0.0, 1.0), motion_limits=motion_limits,
                         motion_properties=motion_properties, mimic=mimic, meta=meta)
        self.articulations.append(a)
        return a

    def joint(self, name, joint_type, parent, child, *, origin=None, axis=None,
              limit=None, dynamics=None, mimic=None, meta=None):
        return self.articulation(name, joint_type, parent, child, origin=origin, axis=axis,
                                 motion_limits=limit, motion_properties=dynamics, mimic=mimic, meta=meta)

    def material(self, name, *, rgba=None, color=None, texture=None):
        m = Material(name, rgba=rgba, color=color, texture=texture)
        self.materials.append(m)
        return m

    def set_assets(self, assets):
        self.assets = assets
        return assets

    # ---- queries ----
    def get_part(self, name):
        key = name if isinstance(name, str) else name.name
        for p in self.parts:
            if p.name == key:
                return p
        raise ValidationError("unknown part %r" % name)

    get_link = get_part

    def get_articulation(self, name):
        key = name if isinstance(name, str) else getattr(name, "name", name)
        for a in self.articulations:
            if a.name == key:
                return a
        raise ValidationError("unknown articulation %r" % name)

    get_joint = get_articulation

    def root_parts(self):
        children = {a.child for a in self.articulations}
        return [p for p in self.parts if p.name not in children]

    root_links = root_parts

    def validate(self, *a, **k):
        return None

    def to_urdf(self, *a, **k):
        raise ValidationError("URDF export is not available in self-contained CadQuery mode")

    # ---- rest-pose world transform per part (URDF forward kinematics, q=0) ----
    def _world_transforms(self):
        parent_of, joint_tf = {}, {}
        for a in self.articulations:
            parent_of[a.child] = a.parent
            joint_tf[a.child] = _Tf.from_origin(a.origin)
        cache = {}

        def world(name):
            if name in cache:
                return cache[name]
            if name in parent_of:
                tf = world(parent_of[name]) @ joint_tf[name]
            else:
                tf = _Tf()
            cache[name] = tf
            return tf

        return {p.name: world(p.name) for p in self.parts}

    # ---- assemble to a CadQuery Assembly in rest pose ----
    def to_cq(self):
        worlds = self._world_transforms()
        asm = cq.Assembly(name=self.name or "model")
        idx = 0
        for part in self.parts:
            wt = worlds.get(part.name, _Tf())
            for vis in part.visuals:
                try:
                    shape = _to_shape(vis.geometry)
                except Exception as exc:
                    raise ValidationError(
                        "part %r visual %r: %s" % (part.name, vis.name, exc)
                    )
                loc = (wt @ _Tf.from_origin(vis.origin)).location()
                rgba = None
                mat = vis.material
                if isinstance(mat, str):
                    mat = next((m for m in self.materials if m.name == mat), None)
                if isinstance(mat, Material) and mat.rgba:
                    rgba = mat.rgba
                kw = {"name": "%s_%d" % (part.name, idx)}
                if rgba:
                    kw["color"] = cq.Color(*rgba)
                asm.add(shape, loc=loc, **kw)
                idx += 1
        return asm

    # convenience aliases a few scripts might call
    def to_assembly(self):
        return self.to_cq()

    def compound(self):
        return self.to_cq().toCompound()

# ===== model =====
import math
import cadquery as cq
def _annular_tube_x(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """A bottom-bracket tube centered on the X axis."""
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((-length / 2.0, 0.0, 0.0))
    )
def _toothed_chainring(
    *,
    tooth_count: int = 42,
    tooth_radius: float = 0.108,
    root_radius: float = 0.101,
    inner_radius: float = 0.066,
    thickness: float = 0.004,
) -> cq.Workplane:
    """Flat narrow-wide style chainring in the local XY plane, thickness on Z."""
    pts = []
    for i in range(tooth_count * 2):
        a = (2.0 * math.pi * i) / (tooth_count * 2)
        # Alternating tooth tips/root valleys give a legible single-ring profile.
        r = tooth_radius if i % 2 == 0 else root_radius
        pts.append((r * math.cos(a), r * math.sin(a)))

    ring = (
        cq.Workplane("XY")
        .polyline(pts)
        .close()
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
    center_cut = (
        cq.Workplane("XY")
        .circle(inner_radius)
        .extrude(thickness * 3.0)
        .translate((0.0, 0.0, -1.5 * thickness))
    )
    ring = ring.cut(center_cut)

    # Five bolt holes on the spider bolt circle.
    bolt_pts = []
    for k in range(5):
        a = math.radians(18.0) + 2.0 * math.pi * k / 5.0
        bolt_pts.append((0.077 * math.cos(a), 0.077 * math.sin(a)))
    bolt_cuts = (
        cq.Workplane("XY")
        .pushPoints(bolt_pts)
        .circle(0.0036)
        .extrude(thickness * 3.0)
        .translate((0.0, 0.0, -1.5 * thickness))
    )
    return ring.cut(bolt_cuts)
def _spider(thickness: float = 0.008) -> cq.Workplane:
    """Five-arm power-meter spider with a hub and wide strain-gauge spokes."""
    spider = (
        cq.Workplane("XY")
        .circle(0.031)
        .circle(0.0105)
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
    for k in range(5):
        a = math.radians(18.0) + 2.0 * math.pi * k / 5.0
        radial = (math.cos(a), math.sin(a))
        tangent = (-math.sin(a), math.cos(a))
        r0, r1 = 0.022, 0.083
        w0, w1 = 0.008, 0.006
        pts = [
            (radial[0] * r0 + tangent[0] * w0, radial[1] * r0 + tangent[1] * w0),
            (radial[0] * r1 + tangent[0] * w1, radial[1] * r1 + tangent[1] * w1),
            (radial[0] * r1 - tangent[0] * w1, radial[1] * r1 - tangent[1] * w1),
            (radial[0] * r0 - tangent[0] * w0, radial[1] * r0 - tangent[1] * w0),
        ]
        arm = (
            cq.Workplane("XY")
            .polyline(pts)
            .close()
            .extrude(thickness)
            .translate((0.0, 0.0, -thickness / 2.0))
        )
        spider = spider.union(arm)
    return spider
def _crank_arm(x_center: float, z_end: float, thickness: float = 0.024) -> cq.Workplane:
    """Tapered hollow-forged crank arm in the YZ plane, extruded along X."""
    sign = 1.0 if z_end >= 0.0 else -1.0
    z_root = sign * 0.020
    root_half_width = 0.018
    end_half_width = 0.013
    body_pts = [
        (-root_half_width, z_root),
        (root_half_width, z_root),
        (end_half_width, z_end),
        (-end_half_width, z_end),
    ]
    body = cq.Workplane("YZ").polyline(body_pts).close().extrude(thickness)

    root_boss = (
        cq.Workplane("YZ")
        .circle(0.030)
        .circle(0.0102)
        .extrude(thickness)
    )
    pedal_boss = (
        cq.Workplane("YZ")
        .center(0.0, z_end)
        .circle(0.018)
        .circle(0.0075)
        .extrude(thickness)
    )

    arm = body.union(root_boss).union(pedal_boss)

    root_cut = (
        cq.Workplane("YZ")
        .circle(0.0102)
        .extrude(thickness * 3.0)
        .translate((-thickness, 0.0, 0.0))
    )
    pedal_cut = (
        cq.Workplane("YZ")
        .center(0.0, z_end)
        .circle(0.0075)
        .extrude(thickness * 3.0)
        .translate((-thickness, 0.0, 0.0))
    )
    arm = arm.cut(root_cut).cut(pedal_cut)

    # Long through-window leaves raised forged rails instead of a solid bar.
    slot = (
        cq.Workplane("YZ")
        .center(0.0, sign * 0.096)
        .rect(0.010, 0.080)
        .extrude(thickness * 3.0)
        .translate((-thickness, 0.0, 0.0))
    )
    arm = arm.cut(slot)
    return arm.translate((x_center - thickness / 2.0, 0.0, 0.0))
def _pedal_body(thickness: float = 0.028) -> cq.Workplane:
    """Compact clipless pedal body with an open spindle window and binding jaws."""
    outer_pts = [
        (-0.036, -0.050),
        (0.036, -0.050),
        (0.044, -0.040),
        (0.044, 0.040),
        (0.036, 0.050),
        (-0.036, 0.050),
        (-0.044, 0.040),
        (-0.044, -0.040),
    ]
    body = (
        cq.Workplane("XY")
        .polyline(outer_pts)
        .close()
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
    # Raised front hook and rear spring bar that make the part read as clipless.
    front_jaw = cq.Workplane("XY").box(0.058, 0.008, 0.010).translate((0.0, 0.034, 0.010))
    rear_jaw = cq.Workplane("XY").box(0.058, 0.010, 0.009).translate((0.0, -0.034, 0.009))
    side_plate_0 = cq.Workplane("XY").box(0.007, 0.062, 0.008).translate((0.036, 0.0, 0.010))
    side_plate_1 = cq.Workplane("XY").box(0.007, 0.062, 0.008).translate((-0.036, 0.0, 0.010))
    return (
        body.union(front_jaw)
        .union(rear_jaw)
        .union(side_plate_0)
        .union(side_plate_1)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="power_meter_crankset")

    shell_mat = model.material("dark_anodized_shell", rgba=(0.05, 0.055, 0.060, 1.0))
    arm_mat = model.material("matte_forged_black", rgba=(0.005, 0.006, 0.007, 1.0))
    ring_mat = model.material("black_chainring", rgba=(0.015, 0.014, 0.012, 1.0))
    metal_mat = model.material("brushed_steel", rgba=(0.68, 0.67, 0.62, 1.0))
    gauge_mat = model.material("amber_gauge_pads", rgba=(0.86, 0.42, 0.10, 1.0))
    pedal_mat = model.material("pedal_black", rgba=(0.02, 0.022, 0.024, 1.0))

    bb_shell = model.part("bb_shell")
    bb_shell.visual(
        mesh_from_cadquery(_annular_tube_x(0.026, 0.016, 0.076), "bb_shell_tube"),
        material=shell_mat,
        name="hollow_shell",
    )
    # Thin silver bearing lips at the shell faces emphasize that the spindle runs
    # through a real hollow bottom bracket rather than through a solid cylinder.
    for idx, x in enumerate((-0.040, 0.040)):
        bb_shell.visual(
            mesh_from_cadquery(_annular_tube_x(0.024, 0.0108, 0.004), f"bearing_lip_{idx}"),
            origin=Origin(xyz=(x, 0.0, 0.0)),
            material=metal_mat,
            name=f"bearing_lip_{idx}",
        )

    crank = model.part("crank_assembly")
    crank.visual(
        Cylinder(radius=0.011, length=0.192),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal_mat,
        name="spindle",
    )
    crank.visual(
        mesh_from_cadquery(_toothed_chainring(), "toothed_chainring"),
        origin=Origin(xyz=(0.054, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=ring_mat,
        name="single_chainring",
    )
    crank.visual(
        mesh_from_cadquery(_spider(), "strain_gauge_spider"),
        origin=Origin(xyz=(0.050, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=arm_mat,
        name="spider",
    )
    crank.visual(
        mesh_from_cadquery(_crank_arm(0.088, -0.175), "drive_crank_arm"),
        material=arm_mat,
        name="arm_0",
    )
    crank.visual(
        mesh_from_cadquery(_crank_arm(-0.088, 0.175), "opposite_crank_arm"),
        material=arm_mat,
        name="arm_1",
    )

    # Five sensor/bridge pads and chainring bolts on the spider face.
    for k in range(5):
        theta = math.radians(18.0) + 2.0 * math.pi * k / 5.0
        y = 0.052 * math.sin(theta)
        z = -0.052 * math.cos(theta)
        crank.visual(
            Box((0.003, 0.007, 0.026)),
            origin=Origin(
                xyz=(0.0528, y, z),
                rpy=(theta - math.pi, 0.0, 0.0),
            ),
            material=gauge_mat,
            name=f"gauge_pad_{k}",
        )
        bolt_y = 0.077 * math.sin(theta)
        bolt_z = -0.077 * math.cos(theta)
        crank.visual(
            Cylinder(radius=0.0042, length=0.004),
            origin=Origin(
                xyz=(0.0560, bolt_y, bolt_z),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            material=metal_mat,
            name=f"chainring_bolt_{k}",
        )

    model.articulation(
        "bb_to_crank",
        ArticulationType.CONTINUOUS,
        parent=bb_shell,
        child=crank,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=80.0, velocity=12.0),
    )

    # Two clipless pedals: each has a continuously rotating spindle carrier and
    # a bounded float/tilt joint through the pedal body's long fore-aft axis.
    pedal_specs = (
        ("0", 1.0, (0.088, 0.0, -0.175)),
        ("1", -1.0, (-0.088, 0.0, 0.175)),
    )
    for suffix, side, joint_xyz in pedal_specs:
        axle = model.part(f"pedal_axle_{suffix}")
        axle.visual(
            Cylinder(radius=0.006, length=0.100),
            origin=Origin(xyz=(side * 0.050, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="spindle",
        )
        axle.visual(
            Cylinder(radius=0.013, length=0.026),
            origin=Origin(xyz=(side * 0.105, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="bearing_barrel",
        )
        axle.visual(
            Cylinder(radius=0.010, length=0.010),
            origin=Origin(xyz=(side * 0.0168, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="threaded_shoulder",
        )
        model.articulation(
            f"crank_to_axle_{suffix}",
            ArticulationType.CONTINUOUS,
            parent=crank,
            child=axle,
            origin=Origin(xyz=joint_xyz),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=6.0, velocity=20.0),
        )

        pedal = model.part(f"pedal_body_{suffix}")
        pedal.visual(
            mesh_from_cadquery(_pedal_body(), f"clipless_pedal_body_{suffix}"),
            material=pedal_mat,
            name="clipless_body",
        )
        pedal.visual(
            Cylinder(radius=0.003, length=0.058),
            origin=Origin(xyz=(0.0, 0.034, 0.016), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="front_hook_pin",
        )
        pedal.visual(
            Cylinder(radius=0.003, length=0.058),
            origin=Origin(xyz=(0.0, -0.035, 0.015), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="rear_spring_pin",
        )
        model.articulation(
            f"axle_to_pedal_{suffix}",
            ArticulationType.REVOLUTE,
            parent=axle,
            child=pedal,
            origin=Origin(xyz=(side * 0.105, 0.0, 0.0)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=4.0, velocity=2.0, lower=-0.18, upper=0.18),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
