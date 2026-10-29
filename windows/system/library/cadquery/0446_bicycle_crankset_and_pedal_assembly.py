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
def _annulus_yz(outer_radius: float, inner_radius: float, length: float, *, x: float = 0.0):
    """Annular cylinder with its axis on local X, authored from a YZ workplane."""
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((x - length / 2.0, 0.0, 0.0))
    )
def _bar_yz(r_inner: float, r_outer: float, width: float, angle_rad: float, thickness: float):
    """Flat radial bar in the YZ plane, extruded along X."""
    uy = math.sin(angle_rad)
    uz = math.cos(angle_rad)
    py = -uz
    pz = uy
    half = width / 2.0
    pts = [
        (r_inner * uy + half * py, r_inner * uz + half * pz),
        (r_outer * uy + half * py, r_outer * uz + half * pz),
        (r_outer * uy - half * py, r_outer * uz - half * pz),
        (r_inner * uy - half * py, r_inner * uz - half * pz),
    ]
    return (
        cq.Workplane("YZ")
        .polyline(pts)
        .close()
        .extrude(thickness)
        .translate((-thickness / 2.0, 0.0, 0.0))
    )
def _bottom_bracket_shell():
    body = _annulus_yz(0.022, 0.012, 0.070)
    # Narrow inner bearing races lightly capture the spindle; the wider body bore
    # stays clear so the shell does not read as a solid rod.
    cup_pos = _annulus_yz(0.026, 0.0088, 0.008, x=0.039)
    cup_neg = _annulus_yz(0.026, 0.0088, 0.008, x=-0.039)
    return body.union(cup_pos).union(cup_neg)
def _crank_arm_shape(direction: int, *, spider: bool):
    """Solid track crank arm. direction=-1 points down, +1 points up."""
    thickness = 0.014
    arm_pts = [
        (-0.016, direction * 0.030),
        (0.016, direction * 0.030),
        (0.010, direction * 0.154),
        (0.015, direction * 0.170),
        (-0.015, direction * 0.170),
        (-0.010, direction * 0.154),
    ]
    arm = (
        cq.Workplane("YZ")
        .polyline(arm_pts)
        .close()
        .extrude(thickness)
        .translate((-thickness / 2.0, 0.0, 0.0))
    )
    boss = _annulus_yz(0.034, 0.0087, thickness)
    pedal_eye = (
        cq.Workplane("YZ")
        .center(0.0, direction * 0.170)
        .circle(0.016)
        .circle(0.006)
        .extrude(thickness)
        .translate((-thickness / 2.0, 0.0, 0.0))
    )
    shape = boss.union(arm).union(pedal_eye)

    if spider:
        for deg in (18, 90, 162, 234, 306):
            angle = math.radians(deg)
            shape = shape.union(_bar_yz(0.026, 0.073, 0.010, angle, thickness))
            y = 0.071 * math.sin(angle)
            z = 0.071 * math.cos(angle)
            boss_pad = (
                cq.Workplane("YZ")
                .center(y, z)
                .circle(0.0085)
                .circle(0.0035)
                .extrude(thickness)
                .translate((-thickness / 2.0, 0.0, 0.0))
            )
            shape = shape.union(boss_pad)

    return shape
def _chainring_shape():
    teeth = 48
    root_radius = 0.099
    tip_radius = 0.108
    inner_radius = 0.052
    thickness = 0.006
    points = []
    for i in range(teeth * 2):
        angle = 2.0 * math.pi * i / (teeth * 2)
        radius = tip_radius if i % 2 == 0 else root_radius
        points.append((radius * math.sin(angle), radius * math.cos(angle)))

    ring = (
        cq.Workplane("YZ")
        .polyline(points)
        .close()
        .extrude(thickness)
        .translate((-thickness / 2.0, 0.0, 0.0))
    )

    center_cut = (
        cq.Workplane("YZ")
        .circle(inner_radius)
        .extrude(thickness + 0.004)
        .translate((-(thickness + 0.004) / 2.0, 0.0, 0.0))
    )
    ring = ring.cut(center_cut)

    # The keyed slot at twelve o'clock makes this read as a keyed track ring
    # rather than a plain circular sprocket.
    key_cut = (
        cq.Workplane("YZ")
        .center(0.0, inner_radius + 0.006)
        .rect(0.010, 0.014)
        .extrude(thickness + 0.004)
        .translate((-(thickness + 0.004) / 2.0, 0.0, 0.0))
    )
    ring = ring.cut(key_cut)

    for deg in (18, 90, 162, 234, 306):
        angle = math.radians(deg)
        y = 0.071 * math.sin(angle)
        z = 0.071 * math.cos(angle)
        bolt_cut = (
            cq.Workplane("YZ")
            .center(y, z)
            .circle(0.0038)
            .extrude(thickness + 0.004)
            .translate((-(thickness + 0.004) / 2.0, 0.0, 0.0))
        )
        ring = ring.cut(bolt_cut)

    return ring
def _pedal_shape(direction: int):
    """Open rectangular track pedal/cage with a continuous axle on local X."""
    body_x = 0.060
    body_y = 0.095
    body_z = 0.026
    center_x = direction * 0.082
    cage = cq.Workplane("XY").box(body_x, body_y, body_z).translate((center_x, 0.0, 0.0))
    window = (
        cq.Workplane("XY")
        .box(0.032, 0.061, body_z * 1.6)
        .translate((center_x, 0.0, 0.0))
    )
    cage = cage.cut(window)

    axle = cq.Workplane("YZ").circle(0.0045).extrude(0.112)
    if direction < 0:
        axle = axle.translate((-0.112, 0.0, 0.0))
    cage = cage.union(axle)

    flange = cq.Workplane("YZ").circle(0.010).extrude(0.003)
    if direction < 0:
        flange = flange.translate((-0.003, 0.0, 0.0))
    cage = cage.union(flange)
    return cage
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="fixie_track_crankset")

    black = Material("black_anodized_aluminum", rgba=(0.01, 0.01, 0.012, 1.0))
    dark = Material("dark_bearing_cups", rgba=(0.06, 0.06, 0.065, 1.0))
    steel = Material("polished_steel", rgba=(0.72, 0.72, 0.70, 1.0))
    silver = Material("brushed_chainring_silver", rgba=(0.82, 0.80, 0.74, 1.0))

    shell = model.part("bottom_bracket")
    shell.visual(
        mesh_from_cadquery(_bottom_bracket_shell(), "bottom_bracket_shell", tolerance=0.0007),
        material=dark,
        name="bearing_shell",
    )

    spindle = model.part("spindle")
    spindle.visual(
        Cylinder(radius=0.009, length=0.168),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="spindle_axle",
    )

    right_arm = model.part("right_arm")
    right_arm.visual(
        mesh_from_cadquery(
            _crank_arm_shape(-1, spider=True), "right_solid_crank_arm", tolerance=0.0007
        ),
        material=black,
        name="right_arm_body",
    )

    left_arm = model.part("left_arm")
    left_arm.visual(
        mesh_from_cadquery(
            _crank_arm_shape(1, spider=False), "left_crank_arm", tolerance=0.0007
        ),
        material=black,
        name="left_arm_body",
    )

    chainring = model.part("chainring")
    chainring.visual(
        mesh_from_cadquery(_chainring_shape(), "keyed_track_chainring", tolerance=0.0006),
        material=silver,
        name="toothed_keyed_ring",
    )

    right_pedal = model.part("right_pedal")
    right_pedal.visual(
        mesh_from_cadquery(_pedal_shape(1), "right_track_pedal", tolerance=0.0007),
        material=black,
        name="right_pedal_cage",
    )

    left_pedal = model.part("left_pedal")
    left_pedal.visual(
        mesh_from_cadquery(_pedal_shape(-1), "left_track_pedal", tolerance=0.0007),
        material=black,
        name="left_pedal_cage",
    )

    spin_limits = MotionLimits(effort=80.0, velocity=12.0)
    pedal_limits = MotionLimits(effort=8.0, velocity=18.0)

    model.articulation(
        "bottom_bracket_to_spindle",
        ArticulationType.CONTINUOUS,
        parent=shell,
        child=spindle,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=spin_limits,
    )
    model.articulation(
        "spindle_to_right_arm",
        ArticulationType.FIXED,
        parent=spindle,
        child=right_arm,
        origin=Origin(xyz=(0.078, 0.0, 0.0)),
    )
    model.articulation(
        "spindle_to_left_arm",
        ArticulationType.FIXED,
        parent=spindle,
        child=left_arm,
        origin=Origin(xyz=(-0.078, 0.0, 0.0)),
    )
    model.articulation(
        "right_arm_to_chainring",
        ArticulationType.FIXED,
        parent=right_arm,
        child=chainring,
        origin=Origin(xyz=(0.010, 0.0, 0.0)),
    )
    model.articulation(
        "right_arm_to_pedal",
        ArticulationType.CONTINUOUS,
        parent=right_arm,
        child=right_pedal,
        origin=Origin(xyz=(0.007, 0.0, -0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=pedal_limits,
    )
    model.articulation(
        "left_arm_to_pedal",
        ArticulationType.CONTINUOUS,
        parent=left_arm,
        child=left_pedal,
        origin=Origin(xyz=(-0.007, 0.0, 0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=pedal_limits,
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
