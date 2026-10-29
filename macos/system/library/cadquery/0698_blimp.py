# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

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

# ===== sweeps (8 syms) =====
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

def _tuple_lerp(a, b, t):
    return tuple(float(xa) + (float(xb) - float(xa)) * float(t) for xa, xb in zip(a, b))

def _tuple_extrapolate(a, b):
    return tuple(2.0 * float(xa) - float(xb) for xa, xb in zip(a, b))

def _sweeps_tuple_distance(a, b):
    return sqrt(sum((float(xa) - float(xb)) * (float(xa) - float(xb)) for xa, xb in zip(a, b)))

def _catmull_rom_interp(a, b, ta, tb, t):
    if abs(tb - ta) <= _EPS:
        return tuple(float(v) for v in a)
    wa = (tb - t) / (tb - ta)
    wb = (t - ta) / (tb - ta)
    return tuple(wa * float(va) + wb * float(vb) for va, vb in zip(a, b))

def _sample_catmull_rom_segment(p0, p1, p2, p3, *, steps, alpha):
    def tj(ti, pa, pb):
        dist = max(_sweeps_tuple_distance(pa, pb), _EPS)
        return ti + dist ** alpha

    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)

    out = []
    for j in range(steps):
        t = t1 + (t2 - t1) * (float(j) / float(steps))
        a1 = _catmull_rom_interp(p0, p1, t0, t1, t)
        a2 = _catmull_rom_interp(p1, p2, t1, t2, t)
        a3 = _catmull_rom_interp(p2, p3, t2, t3, t)
        b1 = _catmull_rom_interp(a1, a2, t0, t2, t)
        b2 = _catmull_rom_interp(a2, a3, t1, t3, t)
        out.append(_catmull_rom_interp(b1, b2, t1, t2, t))
    return out

def _sample_catmull_rom_spline(points, *, samples_per_segment, closed, alpha):
    pts = [tuple(float(v) for v in point) for point in points]
    if len(pts) < 2:
        raise ValueError("Catmull-Rom spline requires at least two points")
    if not (0.0 <= float(alpha) <= 1.0):
        raise ValueError("Catmull-Rom alpha must be in [0, 1]")

    dedup = [pts[0]]
    for point in pts[1:]:
        if _sweeps_tuple_distance(point, dedup[-1]) > _EPS:
            dedup.append(point)

    if len(dedup) < 2:
        raise ValueError("Catmull-Rom spline requires at least two distinct points")

    steps = max(2, int(samples_per_segment))

    if closed:
        ring = list(dedup)
        if _sweeps_tuple_distance(ring[0], ring[-1]) <= _EPS:
            ring.pop()
        if len(ring) < 3:
            raise ValueError("Closed Catmull-Rom spline requires at least three distinct points")

        out = []
        n = len(ring)
        for i in range(n):
            seg = _sample_catmull_rom_segment(
                ring[(i - 1) % n], ring[i], ring[(i + 1) % n], ring[(i + 2) % n],
                steps=steps, alpha=float(alpha),
            )
            out.extend(seg)
        if not out:
            raise ValueError("Closed Catmull-Rom spline produced no samples")
        out.append(out[0])
        return out

    if len(dedup) == 2:
        out = [_tuple_lerp(dedup[0], dedup[1], float(j) / float(steps)) for j in range(steps)]
        out.append(dedup[-1])
        return out

    extended = [
        _tuple_extrapolate(dedup[0], dedup[1]),
        *dedup,
        _tuple_extrapolate(dedup[-1], dedup[-2]),
    ]
    out = []
    for i in range(len(dedup) - 1):
        seg = _sample_catmull_rom_segment(
            extended[i], extended[i + 1], extended[i + 2], extended[i + 3],
            steps=steps, alpha=float(alpha),
        )
        out.extend(seg)
    out.append(dedup[-1])
    return out

def sample_catmull_rom_spline_2d(points, *, samples_per_segment: int = 12,
                                 closed: bool = False, alpha: float = 0.5):
    """Sample a centripetal Catmull-Rom spline through the input 2D points."""
    sampled = _sample_catmull_rom_spline(
        points, samples_per_segment=samples_per_segment, closed=bool(closed), alpha=float(alpha),
    )
    return [(float(x), float(y)) for (x, y) in sampled]

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import atan2, cos, hypot, pi, sin
HULL_CENTER_Z = 7.0
GONDOLA_ORIGIN = (0.0, 0.45, 1.15)
LEFT_POD_ORIGIN = (4.75, -0.55, 5.70)
RIGHT_POD_ORIGIN = (-4.75, -0.55, 5.70)
def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2) ** 0.5
def _midpoint(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
def _rpy_for_cylinder(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    length_xy = hypot(dx, dy)
    yaw = atan2(dy, dx)
    pitch = atan2(length_xy, dz)
    return (0.0, pitch, yaw)
def _add_member(
    part,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    *,
    radius: float,
    material,
    name: str | None = None,
) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_cylinder(a, b)),
        material=material,
        name=name,
    )
def _streamlined_body_mesh(
    control_points: list[tuple[float, float]],
    name: str,
    *,
    segments: int = 72,
    samples_per_segment: int = 10,
):
    outer = sample_catmull_rom_spline_2d(
        control_points,
        samples_per_segment=samples_per_segment,
        closed=False,
    )
    start_z = control_points[0][1]
    end_z = control_points[-1][1]
    profile = [(0.0, start_z)]
    for radius, z in outer[1:-1]:
        profile.append((max(0.0, radius), z))
    profile.append((0.0, end_z))
    geometry = LatheGeometry(profile, segments=segments).rotate_x(-pi / 2.0)
    return mesh_from_geometry(geometry, name)
def _pod_mesh(name: str):
    return _streamlined_body_mesh(
        [
            (0.0, -1.22),
            (0.10, -1.15),
            (0.24, -0.86),
            (0.35, -0.18),
            (0.38, 0.40),
            (0.29, 0.95),
            (0.10, 1.16),
            (0.0, 1.25),
        ],
        name,
        segments=48,
        samples_per_segment=8,
    )
def _add_propeller_visuals(part, *, blade_radius: float, hub_radius: float, material, hub_material) -> None:
    part.visual(
        Cylinder(radius=hub_radius, length=0.30),
        origin=Origin(rpy=(-pi / 2.0, 0.0, 0.0)),
        material=hub_material,
        name="hub",
    )
    part.visual(Sphere(radius=hub_radius * 1.10), material=hub_material, name="spinner")
    for blade_index, angle in enumerate((0.0, 2.0 * pi / 3.0, 4.0 * pi / 3.0)):
        part.visual(
            Box((blade_radius * 1.80, 0.10, 0.032)),
            origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.18, angle, 0.0)),
            material=material,
            name=f"blade_{blade_index}",
        )
def _add_wheel_visuals(
    part,
    *,
    tire_radius: float,
    tire_width: float,
    hub_radius: float,
    hub_width: float,
    tire_material,
    hub_material,
) -> None:
    spin_origin = Origin(rpy=(0.0, pi / 2.0, 0.0))
    part.visual(
        Cylinder(radius=tire_radius, length=tire_width),
        origin=spin_origin,
        material=tire_material,
        name="tire",
    )
    part.visual(
        Cylinder(radius=hub_radius, length=hub_width),
        origin=spin_origin,
        material=hub_material,
        name="hub",
    )
    part.visual(Sphere(radius=hub_radius * 0.60), material=hub_material, name="cap")
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="utility_blimp")

    envelope = model.material("envelope", rgba=(0.78, 0.81, 0.84, 1.0))
    orange = model.material("orange", rgba=(0.86, 0.38, 0.12, 1.0))
    pod_gray = model.material("pod_gray", rgba=(0.39, 0.42, 0.46, 1.0))
    structure = model.material("structure", rgba=(0.29, 0.30, 0.32, 1.0))
    glass = model.material("glass", rgba=(0.63, 0.77, 0.86, 0.40))
    tire = model.material("tire", rgba=(0.05, 0.05, 0.05, 1.0))
    wheel_metal = model.material("wheel_metal", rgba=(0.70, 0.72, 0.75, 1.0))
    prop_black = model.material("prop_black", rgba=(0.08, 0.08, 0.09, 1.0))

    hull = model.part("hull")
    hull.visual(
        _streamlined_body_mesh(
            [
                (0.0, -15.0),
                (0.35, -14.2),
                (1.05, -12.8),
                (2.30, -9.8),
                (3.55, -4.6),
                (4.15, 0.0),
                (4.05, 4.9),
                (3.00, 9.8),
                (1.55, 13.2),
                (0.42, 14.5),
                (0.0, 15.0),
            ],
            "hull_envelope",
        ),
        origin=Origin(xyz=(0.0, 0.0, HULL_CENTER_Z)),
        material=envelope,
        name="envelope",
    )
    hull.visual(
        Box((0.92, 3.60, 0.30)),
        origin=Origin(xyz=(0.0, 0.45, 2.66)),
        material=structure,
        name="gondola_mount",
    )
    hull.visual(
        Box((0.48, 5.20, 0.24)),
        origin=Origin(xyz=(0.0, 0.18, 2.40)),
        material=pod_gray,
        name="keel_fairing",
    )
    hull.visual(
        Box((0.36, 1.25, 0.28)),
        origin=Origin(xyz=(4.17, -0.55, 6.15)),
        material=structure,
        name="left_pod_saddle",
    )
    hull.visual(
        Box((0.36, 1.25, 0.28)),
        origin=Origin(xyz=(-4.17, -0.55, 6.15)),
        material=structure,
        name="right_pod_saddle",
    )
    hull.visual(
        Box((1.30, 2.00, 1.45)),
        origin=Origin(xyz=(0.0, -13.55, 7.0)),
        material=orange,
        name="tail_boom",
    )
    hull.visual(
        Box((0.20, 1.30, 4.70)),
        origin=Origin(xyz=(0.0, -14.55, 7.0)),
        material=orange,
        name="rear_fin",
    )
    hull.visual(
        Box((3.10, 0.95, 0.18)),
        origin=Origin(xyz=(1.55, -13.73, 7.0)),
        material=orange,
        name="left_stabilizer",
    )
    hull.visual(
        Box((3.10, 0.95, 0.18)),
        origin=Origin(xyz=(-1.55, -13.73, 7.0)),
        material=orange,
        name="right_stabilizer",
    )
    hull.visual(
        Sphere(radius=0.18),
        origin=Origin(xyz=(0.0, 15.05, HULL_CENTER_Z)),
        material=wheel_metal,
        name="nose_cap",
    )

    gondola = model.part("gondola")
    gondola.visual(
        Box((2.04, 3.20, 1.15)),
        material=pod_gray,
        name="gondola_shell",
    )
    gondola.visual(
        Box((1.76, 2.92, 0.34)),
        origin=Origin(xyz=(0.0, 0.0, 0.56)),
        material=orange,
        name="roof_cap",
    )
    gondola.visual(
        Box((1.22, 1.72, 0.36)),
        origin=Origin(xyz=(0.0, -0.18, -0.62)),
        material=structure,
        name="belly_box",
    )
    gondola.visual(
        Box((1.38, 0.72, 0.52)),
        origin=Origin(xyz=(0.0, 1.67, 0.10)),
        material=pod_gray,
        name="nose_cabin",
    )
    gondola.visual(
        Box((1.20, 0.06, 0.38)),
        origin=Origin(xyz=(0.0, 1.62, 0.12)),
        material=glass,
        name="front_window",
    )
    gondola.visual(
        Box((0.05, 1.32, 0.34)),
        origin=Origin(xyz=(1.03, 0.55, 0.12)),
        material=glass,
        name="left_window",
    )
    gondola.visual(
        Box((0.05, 1.32, 0.34)),
        origin=Origin(xyz=(-1.03, 0.55, 0.12)),
        material=glass,
        name="right_window",
    )
    gondola.visual(
        Box((0.72, 2.64, 0.10)),
        origin=Origin(xyz=(0.0, 0.12, 0.72)),
        material=structure,
        name="roof_saddle",
    )
    for index, (lower, upper) in enumerate(
        (
            ((0.76, 1.00, 0.60), (0.42, 1.16, 1.338)),
            ((-0.76, 1.00, 0.60), (-0.42, 1.16, 1.338)),
            ((0.74, -1.06, 0.60), (0.40, -1.12, 1.338)),
            ((-0.74, -1.06, 0.60), (-0.40, -1.12, 1.338)),
        )
    ):
        _add_member(
            gondola,
            lower,
            upper,
            radius=0.050,
            material=structure,
            name=f"support_strut_{index}",
        )
    gondola.visual(
        Cylinder(radius=0.050, length=1.68),
        origin=Origin(xyz=(0.0, -0.22, -0.87), rpy=(0.0, pi / 2.0, 0.0)),
        material=structure,
        name="main_axle",
    )
    for index, (upper, lower) in enumerate(
        (
            ((0.52, -0.08, -0.48), (0.86, -0.22, -0.87)),
            ((-0.52, -0.08, -0.48), (-0.86, -0.22, -0.87)),
            ((0.34, 0.42, -0.42), (0.86, -0.22, -0.87)),
            ((-0.34, 0.42, -0.42), (-0.86, -0.22, -0.87)),
        )
    ):
        _add_member(
            gondola,
            upper,
            lower,
            radius=0.040,
            material=structure,
            name=f"main_gear_leg_{index}",
        )
    gondola.visual(
        Cylinder(radius=0.032, length=0.08),
        origin=Origin(xyz=(0.86, -0.22, -0.87), rpy=(0.0, pi / 2.0, 0.0)),
        material=wheel_metal,
        name="left_stub_axle",
    )
    gondola.visual(
        Cylinder(radius=0.032, length=0.08),
        origin=Origin(xyz=(-0.86, -0.22, -0.87), rpy=(0.0, pi / 2.0, 0.0)),
        material=wheel_metal,
        name="right_stub_axle",
    )
    gondola.visual(
        Box((0.34, 0.10, 0.10)),
        origin=Origin(xyz=(0.0, 1.08, -0.58)),
        material=wheel_metal,
        name="nose_fork_crown",
    )
    _add_member(
        gondola,
        (0.0, 0.92, -0.28),
        (0.0, 1.08, -0.58),
        radius=0.040,
        material=structure,
        name="nose_gear_leg",
    )
    _add_member(
        gondola,
        (0.0, 0.42, -0.42),
        (0.0, 0.98, -0.60),
        radius=0.028,
        material=structure,
        name="nose_drag_brace",
    )
    _add_member(
        gondola,
        (0.152, 1.08, -0.58),
        (0.152, 1.18, -0.84),
        radius=0.022,
        material=wheel_metal,
        name="nose_fork_left",
    )
    _add_member(
        gondola,
        (-0.152, 1.08, -0.58),
        (-0.152, 1.18, -0.84),
        radius=0.022,
        material=wheel_metal,
        name="nose_fork_right",
    )

    left_pod = model.part("left_pod")
    left_pod.visual(_pod_mesh("left_pod_body"), material=pod_gray, name="pod_body")
    left_pod.visual(
        Box((0.48, 1.16, 0.16)),
        origin=Origin(xyz=(-0.10, 0.0, 0.46)),
        material=structure,
        name="pylon_fairing",
    )
    _add_member(
        left_pod,
        (-0.16, 0.28, 0.16),
        (-0.40, 0.38, 0.58),
        radius=0.045,
        material=structure,
        name="left_front_pylon",
    )
    _add_member(
        left_pod,
        (-0.16, -0.28, 0.16),
        (-0.40, -0.36, 0.58),
        radius=0.045,
        material=structure,
        name="left_rear_pylon",
    )
    left_pod.visual(
        Cylinder(radius=0.050, length=0.18),
        origin=Origin(xyz=(0.0, 1.12, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=wheel_metal,
        name="shaft",
    )

    right_pod = model.part("right_pod")
    right_pod.visual(_pod_mesh("right_pod_body"), material=pod_gray, name="pod_body")
    right_pod.visual(
        Box((0.48, 1.16, 0.16)),
        origin=Origin(xyz=(0.10, 0.0, 0.46)),
        material=structure,
        name="pylon_fairing",
    )
    _add_member(
        right_pod,
        (0.16, 0.28, 0.16),
        (0.40, 0.38, 0.58),
        radius=0.045,
        material=structure,
        name="right_front_pylon",
    )
    _add_member(
        right_pod,
        (0.16, -0.28, 0.16),
        (0.40, -0.36, 0.58),
        radius=0.045,
        material=structure,
        name="right_rear_pylon",
    )
    right_pod.visual(
        Cylinder(radius=0.050, length=0.18),
        origin=Origin(xyz=(0.0, 1.12, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=wheel_metal,
        name="shaft",
    )

    rudder = model.part("rudder")
    rudder.visual(
        Box((0.16, 0.96, 4.38)),
        origin=Origin(xyz=(0.0, -0.48, 0.0)),
        material=orange,
        name="rudder_surface",
    )

    left_elevator = model.part("left_elevator")
    left_elevator.visual(
        Box((2.44, 0.90, 0.14)),
        origin=Origin(xyz=(0.0, -0.45, 0.0)),
        material=orange,
        name="elevator_surface",
    )

    right_elevator = model.part("right_elevator")
    right_elevator.visual(
        Box((2.44, 0.90, 0.14)),
        origin=Origin(xyz=(0.0, -0.45, 0.0)),
        material=orange,
        name="elevator_surface",
    )

    left_propeller = model.part("left_propeller")
    _add_propeller_visuals(
        left_propeller,
        blade_radius=0.78,
        hub_radius=0.12,
        material=prop_black,
        hub_material=wheel_metal,
    )

    right_propeller = model.part("right_propeller")
    _add_propeller_visuals(
        right_propeller,
        blade_radius=0.78,
        hub_radius=0.12,
        material=prop_black,
        hub_material=wheel_metal,
    )

    left_wheel = model.part("left_wheel")
    _add_wheel_visuals(
        left_wheel,
        tire_radius=0.28,
        tire_width=0.16,
        hub_radius=0.11,
        hub_width=0.20,
        tire_material=tire,
        hub_material=wheel_metal,
    )

    right_wheel = model.part("right_wheel")
    _add_wheel_visuals(
        right_wheel,
        tire_radius=0.28,
        tire_width=0.16,
        hub_radius=0.11,
        hub_width=0.20,
        tire_material=tire,
        hub_material=wheel_metal,
    )

    nose_wheel = model.part("nose_wheel")
    _add_wheel_visuals(
        nose_wheel,
        tire_radius=0.24,
        tire_width=0.12,
        hub_radius=0.09,
        hub_width=0.26,
        tire_material=tire,
        hub_material=wheel_metal,
    )

    model.articulation(
        "hull_to_gondola",
        ArticulationType.FIXED,
        parent=hull,
        child=gondola,
        origin=Origin(xyz=GONDOLA_ORIGIN),
    )
    model.articulation(
        "hull_to_left_pod",
        ArticulationType.FIXED,
        parent=hull,
        child=left_pod,
        origin=Origin(xyz=LEFT_POD_ORIGIN),
    )
    model.articulation(
        "hull_to_right_pod",
        ArticulationType.FIXED,
        parent=hull,
        child=right_pod,
        origin=Origin(xyz=RIGHT_POD_ORIGIN),
    )
    model.articulation(
        "rudder_hinge",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=rudder,
        origin=Origin(xyz=(0.0, -15.20, 7.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5, lower=-0.48, upper=0.48),
    )
    model.articulation(
        "left_elevator_hinge",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=left_elevator,
        origin=Origin(xyz=(2.15, -14.205, 7.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=15.0, velocity=1.5, lower=-0.42, upper=0.42),
    )
    model.articulation(
        "right_elevator_hinge",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=right_elevator,
        origin=Origin(xyz=(-2.15, -14.205, 7.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=15.0, velocity=1.5, lower=-0.42, upper=0.42),
    )
    model.articulation(
        "left_prop_spin",
        ArticulationType.CONTINUOUS,
        parent=left_pod,
        child=left_propeller,
        origin=Origin(xyz=(0.0, 1.40, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=45.0),
    )
    model.articulation(
        "right_prop_spin",
        ArticulationType.CONTINUOUS,
        parent=right_pod,
        child=right_propeller,
        origin=Origin(xyz=(0.0, 1.40, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=45.0),
    )
    model.articulation(
        "left_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=gondola,
        child=left_wheel,
        origin=Origin(xyz=(1.00, -0.22, -0.87)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=6.0, velocity=16.0),
    )
    model.articulation(
        "right_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=gondola,
        child=right_wheel,
        origin=Origin(xyz=(-1.00, -0.22, -0.87)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=6.0, velocity=16.0),
    )
    model.articulation(
        "nose_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=gondola,
        child=nose_wheel,
        origin=Origin(xyz=(0.0, 1.18, -0.88)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=5.0, velocity=16.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
