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

def _points_match_2d(a, b, tol=1e-9):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

def _polygon_area(points):
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area * 0.5

def _ensure_ccw(points):
    area = _polygon_area(points)
    if abs(area) <= 1e-9:
        raise ValidationError("Profile area must be non-zero")
    return list(reversed(points)) if area < 0 else points

def _profile_points_2d(profile):
    points = [(float(x), float(y)) for (x, y) in profile]
    cleaned = []
    for pt in points:
        if not cleaned or not _points_match_2d(cleaned[-1], pt):
            cleaned.append(pt)
    if len(cleaned) >= 2 and _points_match_2d(cleaned[0], cleaned[-1]):
        cleaned = cleaned[:-1]
    if len(cleaned) < 3:
        raise ValidationError("Profile must have at least 3 unique points")
    return cleaned

def _extrude_profile(points, height, *, center=True, z0=None):
    """Extrude a closed 2D profile (XY) by height along +Z. Returns cq.Solid."""
    pts = _ensure_ccw(_profile_points_2d(points))
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for (x, y) in pts], close=True))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, float(height)))
    dz = (-height / 2.0 if center else 0.0) if z0 is None else z0
    if dz:
        solid = solid.translate(cq.Vector(0, 0, dz))
    return solid

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
import cadquery as cq
CRANK_LENGTH = 0.170
DRIVE_Z = 0.055
OPPOSITE_Z = -0.055
CHAINRING_Z = 0.040
def _rotated(points: list[tuple[float, float]], angle: float) -> list[tuple[float, float]]:
    ca, sa = cos(angle), sin(angle)
    return [(x * ca - y * sa, x * sa + y * ca) for x, y in points]
def _capsule_profile(
    x0: float,
    x1: float,
    width: float,
    *,
    segments: int = 14,
    angle: float = 0.0,
) -> list[tuple[float, float]]:
    radius = width / 2.0
    pts: list[tuple[float, float]] = []
    for i in range(segments + 1):
        a = -pi / 2.0 + i * pi / segments
        pts.append((x1 + radius * cos(a), radius * sin(a)))
    for i in range(segments + 1):
        a = pi / 2.0 + i * pi / segments
        pts.append((x0 + radius * cos(a), radius * sin(a)))
    return _rotated(pts, angle)
def _extrude_profile(
    profile: list[tuple[float, float]],
    thickness: float,
    z_center: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .polyline(profile)
        .close()
        .extrude(thickness)
        .translate((0.0, 0.0, z_center - thickness / 2.0))
    )
def _z_cylinder(radius: float, length: float, z_center: float, x: float = 0.0, y: float = 0.0) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((x, y, z_center - length / 2.0))
    )
def _radial_bar(
    r0: float,
    r1: float,
    width: float,
    angle: float,
    thickness: float,
    z_center: float,
) -> cq.Workplane:
    ca, sa = cos(angle), sin(angle)
    px, py = -sa * width / 2.0, ca * width / 2.0
    p0 = (r0 * ca, r0 * sa)
    p1 = (r1 * ca, r1 * sa)
    profile = [
        (p0[0] + px, p0[1] + py),
        (p1[0] + px, p1[1] + py),
        (p1[0] - px, p1[1] - py),
        (p0[0] - px, p0[1] - py),
    ]
    return _extrude_profile(profile, thickness, z_center)
def _crank_arm(angle: float, z_center: float) -> cq.Workplane:
    arm = _extrude_profile(_capsule_profile(0.018, CRANK_LENGTH, 0.030, angle=angle), 0.012, z_center)
    slot = _extrude_profile(_capsule_profile(0.050, 0.132, 0.012, segments=10, angle=angle), 0.018, z_center)
    arm = arm.cut(slot)

    end_x = CRANK_LENGTH * cos(angle)
    end_y = CRANK_LENGTH * sin(angle)
    arm = arm.union(_z_cylinder(0.026, 0.018, z_center))
    arm = arm.union(_z_cylinder(0.017, 0.018, z_center, end_x, end_y))
    return arm
def _chainring_profile(teeth: int = 48) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(teeth * 2):
        angle = 2.0 * pi * i / (teeth * 2)
        radius = 0.112 if i % 2 == 0 else 0.106
        pts.append((radius * cos(angle), radius * sin(angle)))
    return pts
def _make_crank_body() -> cq.Workplane:
    ring_thickness = 0.006
    ring = _extrude_profile(_chainring_profile(), ring_thickness, CHAINRING_Z)
    inner_cut = _z_cylinder(0.086, ring_thickness + 0.006, CHAINRING_Z)
    ring = ring.cut(inner_cut)

    body = ring
    for i in range(5):
        a = pi / 2.0 + i * 2.0 * pi / 5.0
        body = body.union(_radial_bar(0.021, 0.092, 0.014, a, 0.007, CHAINRING_Z))
        bx, by = 0.077 * cos(a), 0.077 * sin(a)
        body = body.union(_z_cylinder(0.0065, 0.008, CHAINRING_Z + 0.001, bx, by))

    body = body.union(_z_cylinder(0.030, 0.020, CHAINRING_Z))
    body = body.union(_z_cylinder(0.017, 0.140, 0.0))
    body = body.union(_crank_arm(-pi / 2.0, DRIVE_Z))
    body = body.union(_crank_arm(pi / 2.0, OPPOSITE_Z))
    return body
def _make_bottom_bracket() -> cq.Workplane:
    shell = _z_cylinder(0.032, 0.082, 0.0).cut(_z_cylinder(0.020, 0.090, 0.0))
    shell = shell.union(_z_cylinder(0.037, 0.008, 0.045).cut(_z_cylinder(0.020, 0.012, 0.045)))
    shell = shell.union(_z_cylinder(0.037, 0.008, -0.045).cut(_z_cylinder(0.020, 0.012, -0.045)))
    return shell
def _make_pedal_body() -> cq.Workplane:
    z_mid = 0.095
    frame = cq.Workplane("XY").box(0.110, 0.066, 0.034).translate((0.0, 0.0, z_mid))
    frame = frame.cut(cq.Workplane("XY").box(0.078, 0.038, 0.050).translate((0.0, 0.0, z_mid)))
    frame = frame.union(cq.Workplane("XY").box(0.104, 0.008, 0.030).translate((0.0, 0.0, z_mid)))
    frame = frame.union(cq.Workplane("XY").box(0.010, 0.058, 0.030).translate((0.0, 0.0, z_mid)))
    frame = frame.union(_z_cylinder(0.012, 0.075, z_mid))

    for z in (0.076, 0.114):
        for x in (-0.040, 0.040):
            for y in (-0.024, 0.024):
                frame = frame.union(_z_cylinder(0.0023, 0.006, z, x, y))
    return frame
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="road_bike_crankset")

    model.material("satin_silver", rgba=(0.72, 0.74, 0.76, 1.0))
    model.material("anodized_black", rgba=(0.02, 0.022, 0.025, 1.0))
    model.material("dark_grey", rgba=(0.10, 0.105, 0.11, 1.0))
    model.material("polished_steel", rgba=(0.82, 0.84, 0.86, 1.0))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(
        mesh_from_cadquery(_make_bottom_bracket(), "bottom_bracket_shell", tolerance=0.0006),
        material="satin_silver",
        name="bb_shell",
    )

    crank_assembly = model.part("crank_assembly")
    crank_assembly.visual(
        mesh_from_cadquery(_make_crank_body(), "spider_chainring_cranks", tolerance=0.0006),
        material="anodized_black",
        name="crank_body",
    )
    for i in range(5):
        a = pi / 2.0 + i * 2.0 * pi / 5.0
        crank_assembly.visual(
            Cylinder(radius=0.0042, length=0.004),
            origin=Origin(xyz=(0.077 * cos(a), 0.077 * sin(a), CHAINRING_Z + 0.0055)),
            material="polished_steel",
            name=f"chainring_bolt_{i}",
        )

    crank_assembly.visual(
        Cylinder(radius=0.006, length=0.115),
        origin=Origin(xyz=(0.0, -CRANK_LENGTH, DRIVE_Z + 0.0575)),
        material="polished_steel",
        name="drive_stub_axle",
    )
    crank_assembly.visual(
        Cylinder(radius=0.006, length=0.115),
        origin=Origin(xyz=(0.0, CRANK_LENGTH, OPPOSITE_Z - 0.0575)),
        material="polished_steel",
        name="opposite_stub_axle",
    )

    drive_pedal = model.part("drive_pedal")
    drive_pedal.visual(
        mesh_from_cadquery(_make_pedal_body(), "drive_platform_pedal", tolerance=0.0006),
        material="dark_grey",
        name="pedal_body",
    )

    opposite_pedal = model.part("opposite_pedal")
    opposite_pedal.visual(
        mesh_from_cadquery(_make_pedal_body(), "opposite_platform_pedal", tolerance=0.0006),
        material="dark_grey",
        name="pedal_body",
    )

    model.articulation(
        "bottom_bracket_spin",
        ArticulationType.REVOLUTE,
        parent=bottom_bracket,
        child=crank_assembly,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=120.0, velocity=8.0, lower=-pi, upper=pi),
    )
    model.articulation(
        "drive_pedal_spin",
        ArticulationType.REVOLUTE,
        parent=crank_assembly,
        child=drive_pedal,
        origin=Origin(xyz=(0.0, -CRANK_LENGTH, DRIVE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=12.0, lower=-pi, upper=pi),
    )
    model.articulation(
        "opposite_pedal_spin",
        ArticulationType.REVOLUTE,
        parent=crank_assembly,
        child=opposite_pedal,
        origin=Origin(xyz=(0.0, CRANK_LENGTH, OPPOSITE_Z), rpy=(pi, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=12.0, lower=-pi, upper=pi),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
