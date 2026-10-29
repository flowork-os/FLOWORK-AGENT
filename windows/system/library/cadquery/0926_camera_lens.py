# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

from __future__ import annotations

import cadquery as cq
import math
from math import acos, atan2, cos, isfinite, pi, sin, sqrt, tan

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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

def mesh_from_geometry(geometry, name=None, **kwargs):
    return _CQMesh(_to_shape(geometry), name=name if isinstance(name, str) else None)

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

def _solid_from_triangles(vertices, faces):
    """Fallback: wrap a raw triangle soup as a B-rep solid (for MeshGeometry
    instances that are authored vertex/face directly)."""
    tri_faces = []
    for (a, b, c) in faces:
        va, vb, vc = vertices[a], vertices[b], vertices[c]
        if va == vb or vb == vc or vc == va:
            continue
        w = cq.Wire.makePolygon([cq.Vector(*va), cq.Vector(*vb), cq.Vector(*vc)], close=True)
        try:
            tri_faces.append(cq.Face.makeFromWires(w))
        except Exception:
            continue
    if not tri_faces:
        raise ValidationError("MeshGeometry: no valid triangles to build a solid")
    shell = cq.Shell.makeShell(tri_faces)
    try:
        return cq.Solid.makeSolid(shell)
    except Exception:
        return cq.Compound.makeCompound(tri_faces)

class MeshGeometry:
    """Base for all geometry families. Subclasses build parametric CadQuery
    B-rep and call ``self._set(shape)``. Supports the mesh-style manipulation
    API (translate/rotate/scale/merge/copy) used by Articraft model scripts,
    applied to the underlying CadQuery shape."""

    def __init__(self, vertices=None, faces=None):
        self.vertices = list(vertices or [])
        self.faces = list(faces or [])
        self._shape = None

    # subclasses call this with their cadquery shape
    def _set(self, shape):
        self._shape = _to_shape(shape) if not isinstance(shape, cq.Shape) else shape
        return self

    def _cq(self):
        if self._shape is not None:
            return self._shape
        return _solid_from_triangles(self.vertices, self.faces)

    # ---- mesh-style authoring (raw triangle fallback path) ----
    def add_vertex(self, x, y, z):
        self.vertices.append((float(x), float(y), float(z)))
        return len(self.vertices) - 1

    def add_face(self, a, b, c):
        self.faces.append((int(a), int(b), int(c)))

    def copy(self):
        g = MeshGeometry(self.vertices, self.faces)
        g._shape = self._shape
        return g

    clone = copy

    # ---- rigid / affine transforms (operate on the cadquery shape) ----
    def translate(self, dx, dy=None, dz=None):
        if dy is None:
            dx, dy, dz = dx
        self._shape = self._cq().translate(cq.Vector(float(dx), float(dy), float(dz)))
        return self

    def rotate(self, axis, angle, *, origin=(0.0, 0.0, 0.0)):
        # Articraft angles are RADIANS; cadquery rotate takes degrees about a line.
        o = cq.Vector(float(origin[0]), float(origin[1]), float(origin[2]))
        a = cq.Vector(float(axis[0]), float(axis[1]), float(axis[2]))
        self._shape = self._cq().rotate(o, o + a, math.degrees(float(angle)))
        return self

    def scale(self, sx, sy=None, sz=None):
        if sy is None:
            sy = sz = sx
        if sz is None:
            sz = sx
        m = cq.Matrix([[float(sx), 0, 0, 0], [0, float(sy), 0, 0], [0, 0, float(sz), 0]])
        self._shape = self._cq().transformGeometry(m)
        return self

    def rotate_x(self, angle):
        return self.rotate((1.0, 0.0, 0.0), angle)

    def rotate_y(self, angle):
        return self.rotate((0.0, 1.0, 0.0), angle)

    def rotate_z(self, angle):
        return self.rotate((0.0, 0.0, 1.0), angle)

    def merge(self, other):
        o = _to_shape(other)
        if self._shape is None and not self.faces:
            self._shape = o          # empty accumulator: adopt other's shape
        else:
            self._shape = self._cq().fuse(o)
        return self

    union = merge

    def cut(self, other):
        self._shape = self._cq().cut(_to_shape(other))
        return self

    def difference(self, other):
        return self.cut(other)

    def intersect(self, other):
        self._shape = self._cq().intersect(_to_shape(other))
        return self

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

def _polyline_points_2d(profile):
    points = [(float(x), float(y)) for (x, y) in profile]
    cleaned = []
    for pt in points:
        if not cleaned or not _points_match_2d(cleaned[-1], pt):
            cleaned.append(pt)
    if len(cleaned) < 2:
        raise ValidationError("Profile must have at least 2 unique points")
    return cleaned

def _revolve_profile(profile_rz, *, angle=360.0):
    """Revolve a closed (r,z) profile about the Z axis. r=radius>=0, z=height.
    Matches Articraft LatheGeometry (profile point (r,z) -> circle of radius r
    at height z)."""
    pts = [(float(r), float(z)) for (r, z) in profile_rz]
    wire = cq.Wire.makePolygon([cq.Vector(r, 0.0, z) for (r, z) in pts], close=True)
    return cq.Solid.revolve(wire, [], float(angle), cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))

# ===== brackets_hinges_bezels (1 syms) =====
_EPS = 1e-9

# ===== lathe_extrude_loft (4 syms) =====
def _lathe_extrude_loft_tuple_distance(a, b):
    return math.sqrt(sum((float(xa) - float(xb)) * (float(xa) - float(xb))
                         for xa, xb in zip(a, b)))

def _lathe_cap_connector(start, end, *, start_tangent, end_tangent, mode, samples):
    """Build a flat or round lip connector between two (r,z) points (verbatim)."""
    if _points_match_2d(start, end):
        return [start]
    if mode == "flat":
        return [start, end]
    if mode != "round":
        raise ValidationError("Lathe cap mode must be 'flat' or 'round'")

    chord_dx = end[0] - start[0]
    chord_dz = end[1] - start[1]
    chord = math.sqrt(chord_dx * chord_dx + chord_dz * chord_dz)
    if chord <= _EPS:
        return [start]

    start_len = math.sqrt(start_tangent[0] * start_tangent[0] + start_tangent[1] * start_tangent[1])
    end_len = math.sqrt(end_tangent[0] * end_tangent[0] + end_tangent[1] * end_tangent[1])
    if start_len <= _EPS or end_len <= _EPS:
        return [start, end]

    handle = min(chord * 0.75, start_len * 0.5, end_len * 0.5)
    if handle <= _EPS:
        return [start, end]

    p1 = (
        start[0] + start_tangent[0] * (handle / start_len),
        start[1] + start_tangent[1] * (handle / start_len),
    )
    p2 = (
        end[0] - end_tangent[0] * (handle / end_len),
        end[1] - end_tangent[1] * (handle / end_len),
    )
    return sample_cubic_bezier_spline_2d(
        [start, p1, p2, end],
        samples_per_segment=max(3, int(samples)),
    )

def _lathe_shell_profile(outer_profile, inner_profile, *, start_cap, end_cap, lip_samples):
    """Build a closed (r,z) shell cross-section from outer+inner walls (verbatim)."""
    outer = _polyline_points_2d(outer_profile)
    inner = _polyline_points_2d(inner_profile)

    same_alignment = _lathe_extrude_loft_tuple_distance(outer[0], inner[0]) + _lathe_extrude_loft_tuple_distance(outer[-1], inner[-1])
    flipped_alignment = _lathe_extrude_loft_tuple_distance(outer[0], inner[-1]) + _lathe_extrude_loft_tuple_distance(outer[-1], inner[0])
    if flipped_alignment < same_alignment:
        inner = list(reversed(inner))

    end_connector = _lathe_cap_connector(
        outer[-1],
        inner[-1],
        start_tangent=(outer[-1][0] - outer[-2][0], outer[-1][1] - outer[-2][1]),
        end_tangent=(inner[-2][0] - inner[-1][0], inner[-2][1] - inner[-1][1]),
        mode=end_cap,
        samples=lip_samples,
    )
    start_connector = _lathe_cap_connector(
        inner[0],
        outer[0],
        start_tangent=(inner[0][0] - inner[1][0], inner[0][1] - inner[1][1]),
        end_tangent=(outer[1][0] - outer[0][0], outer[1][1] - outer[0][1]),
        mode=start_cap,
        samples=lip_samples,
    )

    profile = list(outer)
    profile.extend(end_connector[1:])
    profile.extend(reversed(inner[:-1]))
    profile.extend(start_connector[1:])
    return profile

class LatheGeometry(MeshGeometry):
    """Revolve a closed (r,z) profile 360 deg about the Z axis: a profile point
    (r, z) maps to a circle of radius r at height z."""

    @classmethod
    def from_shell_profiles(cls, outer_profile, inner_profile, *, segments=32,
                            start_cap="flat", end_cap="flat", lip_samples=6):
        profile = _lathe_shell_profile(
            outer_profile, inner_profile,
            start_cap=start_cap, end_cap=end_cap, lip_samples=lip_samples,
        )
        return cls(profile, segments=segments, closed=True)

    def __init__(self, profile, *, segments=32, closed=True):
        super().__init__()
        segments = max(3, int(segments))  # noqa: F841 (exact B-rep circle; mesh resolution N/A)
        points = _profile_points_2d(profile) if closed else _polyline_points_2d(profile)
        if closed:
            points = _ensure_ccw(points)

        normalized = []
        for r, z in points:
            if r < -_EPS:
                raise ValidationError("Lathe profile radii must be non-negative")
            normalized.append((0.0 if abs(r) <= _EPS else float(r), float(z)))

        self._set(_revolve_profile(normalized))

# ===== sweeps (1 syms) =====
def sample_cubic_bezier_spline_2d(control_points, *, samples_per_segment: int = 12):
    """Sample a C1-continuous chained cubic Bezier spline in 2D.

    Control-point layout: ``[P0, P1, P2, P3, P4, P5, P6, ...]`` where each
    additional segment contributes three points and starts at the previous
    segment's end (so ``(n - 1) % 3 == 0``)."""
    pts = [(float(x), float(y)) for (x, y) in control_points]
    if len(pts) < 4:
        raise ValueError("Bezier spline requires at least 4 control points")
    if (len(pts) - 1) % 3 != 0:
        raise ValueError("Bezier spline control points must satisfy (n-1) % 3 == 0")

    seg_count = (len(pts) - 1) // 3
    steps = max(2, int(samples_per_segment))

    def eval_seg(p0, p1, p2, p3, t):
        u = 1.0 - t
        b0 = u * u * u
        b1 = 3.0 * u * u * t
        b2 = 3.0 * u * t * t
        b3 = t * t * t
        x = b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0]
        y = b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]
        return (x, y)

    out = []
    for seg in range(seg_count):
        i = seg * 3
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for j in range(steps):
            if seg > 0 and j == 0:
                continue
            t = float(j) / float(steps)
            out.append(eval_seg(p0, p1, p2, p3, t))
    out.append(pts[-1])
    return out

# ===== model =====
import math
def _annular_tube(
    inner_radius: float,
    outer_radius: float,
    length: float,
    *,
    segments: int = 96,
) -> MeshGeometry:
    """Watertight annular cylinder centered on the local Z axis."""

    geom = MeshGeometry()
    z0 = -length / 2.0
    z1 = length / 2.0
    inner0: list[int] = []
    inner1: list[int] = []
    outer0: list[int] = []
    outer1: list[int] = []

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        c = math.cos(theta)
        s = math.sin(theta)
        inner0.append(geom.add_vertex(inner_radius * c, inner_radius * s, z0))
        inner1.append(geom.add_vertex(inner_radius * c, inner_radius * s, z1))
        outer0.append(geom.add_vertex(outer_radius * c, outer_radius * s, z0))
        outer1.append(geom.add_vertex(outer_radius * c, outer_radius * s, z1))

    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(outer0[i], outer0[j], outer1[j])
        geom.add_face(outer0[i], outer1[j], outer1[i])
        geom.add_face(inner0[j], inner0[i], inner1[i])
        geom.add_face(inner0[j], inner1[i], inner1[j])
        geom.add_face(inner1[i], outer1[i], outer1[j])
        geom.add_face(inner1[i], outer1[j], inner1[j])
        geom.add_face(inner0[i], inner0[j], outer0[j])
        geom.add_face(inner0[i], outer0[j], outer0[i])

    return geom
def _ribbed_ring(
    inner_radius: float,
    outer_radius: float,
    length: float,
    *,
    rib_depth: float,
    rib_count: int,
    segments: int = 144,
) -> MeshGeometry:
    """Rubber grip ring with fine longitudinal ribs and a true central bore."""

    geom = MeshGeometry()
    z0 = -length / 2.0
    z1 = length / 2.0
    inner0: list[int] = []
    inner1: list[int] = []
    outer0: list[int] = []
    outer1: list[int] = []

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        # Raised, rounded ridges rather than a perfectly smooth sleeve.
        crest = max(0.0, math.cos(rib_count * theta)) ** 2.6
        local_outer = outer_radius + rib_depth * crest
        c = math.cos(theta)
        s = math.sin(theta)
        inner0.append(geom.add_vertex(inner_radius * c, inner_radius * s, z0))
        inner1.append(geom.add_vertex(inner_radius * c, inner_radius * s, z1))
        outer0.append(geom.add_vertex(local_outer * c, local_outer * s, z0))
        outer1.append(geom.add_vertex(local_outer * c, local_outer * s, z1))

    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(outer0[i], outer0[j], outer1[j])
        geom.add_face(outer0[i], outer1[j], outer1[i])
        geom.add_face(inner0[j], inner0[i], inner1[i])
        geom.add_face(inner0[j], inner1[i], inner1[j])
        geom.add_face(inner1[i], outer1[i], outer1[j])
        geom.add_face(inner1[i], outer1[j], inner1[j])
        geom.add_face(inner0[i], inner0[j], outer0[j])
        geom.add_face(inner0[i], outer0[j], outer0[i])

    return geom
def _biconvex_lens(
    radius: float,
    center_thickness: float,
    edge_thickness: float,
    *,
    radial_samples: int = 14,
    segments: int = 96,
) -> MeshGeometry:
    """Transparent optical element with curved front and rear faces."""

    geom = MeshGeometry()
    front_center = geom.add_vertex(0.0, 0.0, center_thickness / 2.0)
    back_center = geom.add_vertex(0.0, 0.0, -center_thickness / 2.0)
    front_rings: list[list[int]] = []
    back_rings: list[list[int]] = []

    for sample in range(1, radial_samples + 1):
        r = radius * sample / radial_samples
        curvature = 1.0 - (r / radius) ** 2
        half_t = edge_thickness / 2.0 + (center_thickness - edge_thickness) * curvature / 2.0
        front_loop: list[int] = []
        back_loop: list[int] = []
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            front_loop.append(geom.add_vertex(x, y, half_t))
            back_loop.append(geom.add_vertex(x, y, -half_t))
        front_rings.append(front_loop)
        back_rings.append(back_loop)

    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(front_center, front_rings[0][i], front_rings[0][j])
        geom.add_face(back_center, back_rings[0][j], back_rings[0][i])

    for ring_index in range(radial_samples - 1):
        fr0 = front_rings[ring_index]
        fr1 = front_rings[ring_index + 1]
        br0 = back_rings[ring_index]
        br1 = back_rings[ring_index + 1]
        for i in range(segments):
            j = (i + 1) % segments
            geom.add_face(fr0[i], fr1[i], fr1[j])
            geom.add_face(fr0[i], fr1[j], fr0[j])
            geom.add_face(br0[i], br0[j], br1[j])
            geom.add_face(br0[i], br1[j], br1[i])

    front_outer = front_rings[-1]
    back_outer = back_rings[-1]
    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(back_outer[i], back_outer[j], front_outer[j])
        geom.add_face(back_outer[i], front_outer[j], front_outer[i])

    return geom
def _radial_box_origin(radius: float, angle_deg: float, z: float) -> Origin:
    theta = math.radians(angle_deg)
    return Origin(
        xyz=(radius * math.cos(theta), radius * math.sin(theta), z),
        rpy=(0.0, 0.0, theta),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="professional_camera_lens")

    anodized = model.material("satin_black_anodized", rgba=(0.015, 0.015, 0.014, 1.0))
    black = model.material("deep_matte_black", rgba=(0.004, 0.004, 0.004, 1.0))
    rubber = model.material("ribbed_black_rubber", rgba=(0.010, 0.010, 0.009, 1.0))
    white = model.material("engraved_white_paint", rgba=(0.92, 0.90, 0.84, 1.0))
    gold = model.material("thin_gold_accent", rgba=(0.92, 0.62, 0.18, 1.0))
    red = model.material("red_mount_index", rgba=(0.90, 0.04, 0.02, 1.0))
    metal = model.material("brushed_steel_mount", rgba=(0.58, 0.57, 0.54, 1.0))
    glass = model.material("blue_green_coated_glass", rgba=(0.30, 0.62, 0.76, 0.46))
    dark_glass = model.material("deep_internal_glass", rgba=(0.02, 0.08, 0.11, 0.62))

    barrel = model.part("barrel")

    # Continuous hollow stepped shell: rear metal mount, low core under both
    # rotating rings, proud shoulders, and a broad front filter rim.
    barrel_shell = LatheGeometry.from_shell_profiles(
        [
            (0.034, -0.086),
            (0.036, -0.081),
            (0.036, -0.072),
            (0.040, -0.070),
            (0.040, -0.058),
            (0.036, -0.056),
            (0.036, -0.044),
            (0.029, -0.042),
            (0.029, 0.016),
            (0.042, 0.018),
            (0.042, 0.028),
            (0.029, 0.030),
            (0.029, 0.082),
            (0.042, 0.084),
            (0.042, 0.095),
            (0.039, 0.098),
            (0.039, 0.125),
            (0.045, 0.128),
            (0.045, 0.147),
            (0.041, 0.152),
        ],
        [
            (0.020, -0.086),
            (0.020, -0.050),
            (0.022, 0.020),
            (0.024, 0.085),
            (0.028, 0.120),
            (0.030, 0.152),
        ],
        segments=128,
        start_cap="flat",
        end_cap="flat",
        lip_samples=6,
    )
    barrel.visual(
        mesh_from_geometry(barrel_shell, "barrel_shell"),
        material=anodized,
        name="barrel_shell",
    )

    # Individual named shoulders are slightly embedded in the main shell so the
    # rotating rings read as captured between hard mechanical stops.
    barrel.visual(
        mesh_from_geometry(_annular_tube(0.029, 0.0425, 0.004), "zoom_rear_shoulder"),
        origin=Origin(xyz=(0.0, 0.0, -0.044)),
        material=anodized,
        name="zoom_rear_shoulder",
    )
    barrel.visual(
        mesh_from_geometry(_annular_tube(0.029, 0.0425, 0.004), "separator_shoulder"),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material=anodized,
        name="separator_shoulder",
    )
    barrel.visual(
        mesh_from_geometry(_annular_tube(0.029, 0.0425, 0.004), "focus_front_shoulder"),
        origin=Origin(xyz=(0.0, 0.0, 0.0845)),
        material=anodized,
        name="focus_front_shoulder",
    )

    barrel.visual(
        mesh_from_geometry(_annular_tube(0.041, 0.0433, 0.0032), "gold_accent_band"),
        origin=Origin(xyz=(0.0, 0.0, 0.096)),
        material=gold,
        name="gold_accent_band",
    )
    barrel.visual(
        mesh_from_geometry(_annular_tube(0.026, 0.040, 0.005), "front_glass_retainer"),
        origin=Origin(xyz=(0.0, 0.0, 0.136)),
        material=black,
        name="front_glass_retainer",
    )
    barrel.visual(
        mesh_from_geometry(_annular_tube(0.015, 0.026, 0.003), "aperture_stop"),
        origin=Origin(xyz=(0.0, 0.0, 0.067)),
        material=black,
        name="aperture_stop",
    )
    barrel.visual(
        mesh_from_geometry(_annular_tube(0.0172, 0.024, 0.004), "rear_glass_retainer"),
        origin=Origin(xyz=(0.0, 0.0, 0.056)),
        material=black,
        name="rear_glass_retainer",
    )
    barrel.visual(
        mesh_from_geometry(_biconvex_lens(0.0275, 0.009, 0.0024), "front_element"),
        origin=Origin(xyz=(0.0, 0.0, 0.138)),
        material=glass,
        name="front_element",
    )
    barrel.visual(
        mesh_from_geometry(_biconvex_lens(0.0185, 0.007, 0.002), "rear_element"),
        origin=Origin(xyz=(0.0, 0.0, 0.056)),
        material=dark_glass,
        name="rear_element",
    )

    # Three bayonet tabs and a red alignment dot make the rear read as a real
    # interchangeable-lens mount.
    for idx, angle in enumerate((18.0, 138.0, 258.0)):
        barrel.visual(
            Box((0.012, 0.022, 0.0035)),
            origin=_radial_box_origin(0.0405, angle, -0.084),
            material=metal,
            name=f"bayonet_tab_{idx}",
        )
    barrel.visual(
        Sphere(0.0022),
        origin=_radial_box_origin(0.0357, 78.0, -0.052),
        material=red,
        name="mount_index_dot",
    )

    # Stationary white witness line on the fixed barrel.
    barrel.visual(
        Box((0.0011, 0.0035, 0.008)),
        origin=_radial_box_origin(0.0430, 92.0, 0.023),
        material=white,
        name="barrel_index_line",
    )

    zoom_ring = model.part("zoom_ring")
    zoom_ring.visual(
        mesh_from_geometry(
            _ribbed_ring(0.0335, 0.0405, 0.058, rib_depth=0.0017, rib_count=42),
            "zoom_grip",
        ),
        material=rubber,
        name="zoom_grip",
    )
    for idx, angle in enumerate((-34.0, -18.0, 0.0, 19.0, 39.0)):
        zoom_ring.visual(
            Box((0.0030, 0.0030, 0.012 + 0.002 * (idx % 2))),
            origin=_radial_box_origin(0.0417, angle, 0.015),
            material=white,
            name=f"zoom_tick_{idx}",
        )
    zoom_ring.visual(
        Box((0.0030, 0.0042, 0.020)),
        origin=_radial_box_origin(0.0419, 0.0, -0.016),
        material=white,
        name="zoom_marker",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_geometry(
            _ribbed_ring(0.0335, 0.0398, 0.053, rib_depth=0.0012, rib_count=58),
            "focus_grip",
        ),
        material=rubber,
        name="focus_grip",
    )
    for idx, angle in enumerate((-52.0, -32.0, -12.0, 12.0, 34.0, 54.0)):
        focus_ring.visual(
            Box((0.0025, 0.0024, 0.010 + 0.002 * (idx == 2 or idx == 3))),
            origin=_radial_box_origin(0.0408, angle, -0.010),
            material=white,
            name=f"focus_tick_{idx}",
        )
    focus_ring.visual(
        Box((0.0025, 0.0040, 0.018)),
        origin=_radial_box_origin(0.0410, 0.0, 0.014),
        material=white,
        name="focus_marker",
    )

    model.articulation(
        "barrel_to_zoom_ring",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=zoom_ring,
        origin=Origin(xyz=(0.0, 0.0, -0.013)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.9, velocity=3.0, lower=-0.05, upper=1.25),
    )
    model.articulation(
        "barrel_to_focus_ring",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=focus_ring,
        origin=Origin(xyz=(0.0, 0.0, 0.056)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.55, velocity=4.0, lower=-1.35, upper=1.35),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
