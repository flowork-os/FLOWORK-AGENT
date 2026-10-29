# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, jet_engine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: jet_engine

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

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

# ===== primitives (2 syms) =====
class CylinderGeometry(MeshGeometry):
    def __init__(self, radius, height, *, radial_segments=24, closed=True):
        super().__init__()
        radius = float(radius)
        height = float(height)
        solid = cq.Solid.makeCylinder(
            radius, height, cq.Vector(0, 0, -height / 2.0), cq.Vector(0, 0, 1)
        )
        self._set(solid)

class ConeGeometry(MeshGeometry):
    def __init__(self, radius, height, *, radial_segments=24, closed=True):
        super().__init__()
        radius = float(radius)
        height = float(height)
        # apex at +height/2 (radius 0), base radius `radius` at -height/2
        solid = cq.Solid.makeCone(
            radius, 0.0, height, cq.Vector(0, 0, -height / 2.0), cq.Vector(0, 0, 1)
        )
        self._set(solid)

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
ASSETS = AssetContext.from_script(__file__)
def _save_mesh(name: str, geometry: MeshGeometry):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(name))
def _merge_geometries(*geometries: MeshGeometry) -> MeshGeometry:
    merged = MeshGeometry()
    for geometry in geometries:
        merged.merge(geometry)
    return merged
def _loft_profiles_mesh(
    profiles: list[list[tuple[float, float, float]]],
    *,
    closed: bool = True,
    cap_start: bool = False,
    cap_end: bool = False,
) -> MeshGeometry:
    mesh = MeshGeometry()
    if not profiles:
        return mesh

    point_count = len(profiles[0])
    vertex_rows: list[list[int]] = []
    for profile in profiles:
        row = [mesh.add_vertex(x, y, z) for x, y, z in profile]
        vertex_rows.append(row)

    span = point_count if closed else point_count - 1
    for row_index in range(len(vertex_rows) - 1):
        row_a = vertex_rows[row_index]
        row_b = vertex_rows[row_index + 1]
        for point_index in range(span):
            next_index = (point_index + 1) % point_count
            if not closed and next_index >= point_count:
                continue
            a0 = row_a[point_index]
            a1 = row_a[next_index]
            b1 = row_b[next_index]
            b0 = row_b[point_index]
            mesh.add_face(a0, a1, b1)
            mesh.add_face(a0, b1, b0)

    def add_cap(row: list[int], reverse: bool) -> None:
        profile = profiles[0] if row is vertex_rows[0] else profiles[-1]
        cx = sum(point[0] for point in profile) / len(profile)
        cy = sum(point[1] for point in profile) / len(profile)
        cz = sum(point[2] for point in profile) / len(profile)
        center = mesh.add_vertex(cx, cy, cz)
        for point_index in range(point_count):
            next_index = (point_index + 1) % point_count
            if reverse:
                mesh.add_face(center, row[next_index], row[point_index])
            else:
                mesh.add_face(center, row[point_index], row[next_index])

    if cap_start:
        add_cap(vertex_rows[0], reverse=True)
    if cap_end:
        add_cap(vertex_rows[-1], reverse=False)

    return mesh
def _c_shell_profile(
    z: float,
    outer_radius: float,
    inner_radius: float,
    start_angle: float,
    end_angle: float,
    segments: int = 32,
):
    angles = [start_angle + ((end_angle - start_angle) * i / segments) for i in range(segments + 1)]
    outer = [(outer_radius * math.cos(angle), outer_radius * math.sin(angle), z) for angle in angles]
    inner = [(inner_radius * math.cos(angle), inner_radius * math.sin(angle), z) for angle in reversed(angles)]
    return outer + inner
def _full_ring_geometry(z0: float, z1: float, outer_radius: float, inner_radius: float, segments: int = 48):
    return LatheGeometry(
        [
            (inner_radius, z0),
            (outer_radius, z0),
            (outer_radius, z1),
            (inner_radius, z1),
        ],
        segments=segments,
    )
def _shell_from_sections(
    sections: list[tuple[float, float, float]],
    start_angle: float,
    end_angle: float,
    segments: int = 32,
):
    profiles = [
        _c_shell_profile(
            z=station,
            outer_radius=outer_radius,
            inner_radius=inner_radius,
            start_angle=start_angle,
            end_angle=end_angle,
            segments=segments,
        )
        for station, outer_radius, inner_radius in sections
    ]
    return _loft_profiles_mesh(profiles, closed=True, cap_start=False, cap_end=False)
def _blade_section(
    radius: float,
    chord: float,
    thickness: float,
    z_pos: float,
    sweep_y: float,
    twist: float,
):
    chord_y = math.sin(twist)
    chord_z = math.cos(twist)
    thick_y = math.cos(twist)
    thick_z = -math.sin(twist)
    return [
        (
            radius,
            sweep_y + 0.55 * chord * chord_y,
            z_pos + 0.55 * chord * chord_z,
        ),
        (
            radius,
            sweep_y + 0.05 * chord * chord_y + 0.50 * thickness * thick_y,
            z_pos + 0.05 * chord * chord_z + 0.50 * thickness * thick_z,
        ),
        (
            radius,
            sweep_y - 0.45 * chord * chord_y,
            z_pos - 0.45 * chord * chord_z,
        ),
        (
            radius,
            sweep_y + 0.05 * chord * chord_y - 0.50 * thickness * thick_y,
            z_pos + 0.05 * chord * chord_z - 0.50 * thickness * thick_z,
        ),
    ]
def _blade_geometry(stations: list[tuple[float, float, float, float, float, float]]):
    profiles = [
        _blade_section(
            radius=radius,
            chord=chord,
            thickness=thickness,
            z_pos=z_pos,
            sweep_y=sweep_y,
            twist=twist,
        )
        for radius, chord, thickness, z_pos, sweep_y, twist in stations
    ]
    return _loft_profiles_mesh(profiles, closed=True, cap_start=True, cap_end=True)
def _replicate_around_z(base_geometry: MeshGeometry, count: int, angle_offset: float = 0.0):
    replicated = MeshGeometry()
    for index in range(count):
        replicated.merge(base_geometry.clone().rotate_z(angle_offset + (2.0 * math.pi * index / count)))
    return replicated
def _rotate_engine_axis(geometry: MeshGeometry):
    return geometry.rotate_y(math.pi / 2.0)
def _fan_rotor_hub_geometry():
    spinner_profile = [
        (0.0, -0.135),
        (0.022, -0.120),
        (0.085, -0.055),
        (0.116, -0.004),
        (0.122, 0.025),
        (0.112, 0.080),
        (0.082, 0.122),
        (0.0, 0.122),
    ]
    hub_lathe = LatheGeometry(spinner_profile, segments=64)
    root_drum = CylinderGeometry(radius=0.125, height=0.100, radial_segments=48).translate(0.0, 0.0, 0.038)
    return _merge_geometries(hub_lathe, root_drum)
def _fan_blade_geometry():
    blade = _blade_geometry(
        [
            (0.118, 0.230, 0.030, -0.020, -0.008, -0.95),
            (0.250, 0.155, 0.020, 0.015, -0.030, -0.42),
            (0.425, 0.094, 0.012, 0.042, -0.060, -0.05),
        ]
    )
    return _replicate_around_z(blade, count=18, angle_offset=math.pi / 18.0)
def _stator_geometry():
    outer_ring = _full_ring_geometry(z0=-0.012, z1=0.030, outer_radius=0.470, inner_radius=0.432, segments=56)
    inner_hub = LatheGeometry(
        [
            (0.0, -0.018),
            (0.070, -0.006),
            (0.102, 0.016),
            (0.106, 0.108),
            (0.092, 0.220),
            (0.075, 0.300),
            (0.0, 0.300),
        ],
        segments=56,
    )
    vane = _blade_geometry(
        [
            (0.126, 0.115, 0.018, -0.014, -0.010, -0.28),
            (0.270, 0.090, 0.014, 0.016, -0.020, -0.08),
            (0.440, 0.070, 0.010, 0.060, -0.032, 0.08),
        ]
    )
    vanes = _replicate_around_z(vane, count=12, angle_offset=math.pi / 12.0)
    return _merge_geometries(outer_ring, inner_hub, vanes)
def _engine_case_shell_geometry():
    sections = [
        (-0.165, 0.500, 0.438),
        (-0.085, 0.532, 0.450),
        (0.020, 0.540, 0.462),
        (0.220, 0.530, 0.470),
        (0.520, 0.500, 0.440),
        (0.820, 0.455, 0.400),
        (1.060, 0.410, 0.355),
        (1.180, 0.378, 0.330),
    ]
    return _shell_from_sections(
        sections,
        start_angle=0.78 * math.pi,
        end_angle=2.22 * math.pi,
        segments=42,
    )
def _core_case_shell_geometry():
    sections = [
        (-0.010, 0.168, 0.152),
        (0.100, 0.180, 0.164),
        (0.220, 0.196, 0.178),
        (0.360, 0.228, 0.208),
        (0.500, 0.214, 0.196),
        (0.640, 0.175, 0.158),
        (0.780, 0.132, 0.116),
    ]
    shell = _shell_from_sections(
        sections,
        start_angle=0.73 * math.pi,
        end_angle=2.27 * math.pi,
        segments=34,
    )
    front_flange = _full_ring_geometry(z0=-0.012, z1=0.028, outer_radius=0.168, inner_radius=0.060, segments=52)
    return _merge_geometries(shell, front_flange)
def _core_nozzle_accent_geometry():
    sections = [
        (0.540, 0.176, 0.160),
        (0.660, 0.142, 0.126),
        (0.795, 0.106, 0.092),
    ]
    return _shell_from_sections(
        sections,
        start_angle=0.73 * math.pi,
        end_angle=2.27 * math.pi,
        segments=28,
    )
def _compressor_stage_geometry(
    z_center: float,
    disk_radius: float,
    tip_radius: float,
    chord_root: float,
    chord_tip: float,
    thickness_root: float,
    thickness_tip: float,
    blade_count: int,
    twist_root: float,
    twist_tip: float,
):
    disk = CylinderGeometry(radius=disk_radius, height=0.016, radial_segments=42).translate(0.0, 0.0, z_center)
    blade = _blade_geometry(
        [
            (disk_radius * 0.96, chord_root, thickness_root, z_center - 0.012, -0.004, twist_root),
            ((disk_radius + tip_radius) * 0.50, (chord_root + chord_tip) * 0.50, (thickness_root + thickness_tip) * 0.50, z_center, -0.010, (twist_root + twist_tip) * 0.50),
            (tip_radius, chord_tip, thickness_tip, z_center + 0.014, -0.016, twist_tip),
        ]
    )
    blades = _replicate_around_z(blade, count=blade_count, angle_offset=math.pi / blade_count)
    return _merge_geometries(disk, blades)
def _turbine_stage_geometry(
    z_center: float,
    disk_radius: float,
    tip_radius: float,
    chord_root: float,
    chord_tip: float,
    thickness_root: float,
    thickness_tip: float,
    blade_count: int,
    twist_root: float,
    twist_tip: float,
):
    disk = CylinderGeometry(radius=disk_radius, height=0.018, radial_segments=42).translate(0.0, 0.0, z_center)
    blade = _blade_geometry(
        [
            (disk_radius * 0.94, chord_root, thickness_root, z_center - 0.016, 0.004, twist_root),
            ((disk_radius + tip_radius) * 0.50, (chord_root + chord_tip) * 0.50, (thickness_root + thickness_tip) * 0.50, z_center, 0.014, (twist_root + twist_tip) * 0.50),
            (tip_radius, chord_tip, thickness_tip, z_center + 0.018, 0.022, twist_tip),
        ]
    )
    blades = _replicate_around_z(blade, count=blade_count, angle_offset=math.pi / blade_count)
    return _merge_geometries(disk, blades)
def _core_rotor_body_geometry():
    shaft = CylinderGeometry(radius=0.036, height=0.790, radial_segments=36).translate(0.0, 0.0, 0.395)
    drum = LatheGeometry(
        [
            (0.0, 0.000),
            (0.058, 0.000),
            (0.078, 0.160),
            (0.070, 0.320),
            (0.062, 0.520),
            (0.045, 0.720),
            (0.0, 0.790),
        ],
        segments=52,
    )
    tail_cone = ConeGeometry(radius=0.082, height=0.170, radial_segments=42).translate(0.0, 0.0, 0.705)
    return _merge_geometries(shaft, drum, tail_cone)
def _core_compressor_geometry():
    stages = [
        _compressor_stage_geometry(0.070, 0.090, 0.116, 0.060, 0.040, 0.010, 0.006, 20, -0.60, -0.20),
        _compressor_stage_geometry(0.150, 0.106, 0.134, 0.062, 0.042, 0.010, 0.006, 22, -0.58, -0.18),
        _compressor_stage_geometry(0.240, 0.122, 0.152, 0.064, 0.044, 0.010, 0.006, 24, -0.54, -0.14),
        _compressor_stage_geometry(0.335, 0.138, 0.170, 0.066, 0.046, 0.010, 0.006, 26, -0.46, -0.10),
    ]
    return _merge_geometries(*stages)
def _core_turbine_geometry():
    stages = [
        _turbine_stage_geometry(0.535, 0.108, 0.162, 0.068, 0.054, 0.010, 0.008, 18, 0.36, 0.10),
        _turbine_stage_geometry(0.630, 0.096, 0.148, 0.062, 0.048, 0.010, 0.008, 20, 0.32, 0.08),
    ]
    return _merge_geometries(*stages)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cutaway_turbofan_engine", assets=ASSETS)

    nacelle_paint = model.material("nacelle_paint", rgba=(0.86, 0.87, 0.89, 1.0))
    titanium = model.material("titanium", rgba=(0.65, 0.66, 0.69, 1.0))
    brushed_steel = model.material("brushed_steel", rgba=(0.54, 0.56, 0.58, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.23, 0.24, 0.26, 1.0))
    carbon_composite = model.material("carbon_composite", rgba=(0.10, 0.11, 0.12, 1.0))
    heat_stained = model.material("heat_stained", rgba=(0.46, 0.41, 0.36, 1.0))

    engine_case = model.part("engine_case")
    engine_case.visual(
        _save_mesh("engine_case_shell.obj", _rotate_engine_axis(_engine_case_shell_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=nacelle_paint,
        name="outer_shell",
    )
    engine_case.visual(
        _save_mesh("engine_case_stator.obj", _rotate_engine_axis(_stator_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=titanium,
        name="stator_frame",
    )
    engine_case.inertial = Inertial.from_geometry(
        Cylinder(radius=0.500, length=1.345),
        mass=95.0,
        origin=Origin(xyz=(0.507, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    fan_rotor = model.part("fan_rotor")
    fan_rotor.visual(
        _save_mesh("fan_hub.obj", _rotate_engine_axis(_fan_rotor_hub_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=titanium,
        name="fan_hub",
    )
    fan_rotor.visual(
        _save_mesh("fan_blades.obj", _rotate_engine_axis(_fan_blade_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=carbon_composite,
        name="fan_blades",
    )
    fan_rotor.inertial = Inertial.from_geometry(
        Cylinder(radius=0.425, length=0.270),
        mass=34.0,
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    core_casing = model.part("core_casing")
    core_casing.visual(
        _save_mesh("core_case_shell.obj", _rotate_engine_axis(_core_case_shell_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=brushed_steel,
        name="compressor_case",
    )
    core_casing.visual(
        _save_mesh("core_nozzle.obj", _rotate_engine_axis(_core_nozzle_accent_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=heat_stained,
        name="hot_nozzle",
    )
    core_casing.inertial = Inertial.from_geometry(
        Cylinder(radius=0.225, length=0.810),
        mass=26.0,
        origin=Origin(xyz=(0.390, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    core_rotor = model.part("core_rotor")
    core_rotor.visual(
        _save_mesh("core_rotor_body.obj", _rotate_engine_axis(_core_rotor_body_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=dark_steel,
        name="shaft_and_drum",
    )
    core_rotor.visual(
        _save_mesh("core_compressor.obj", _rotate_engine_axis(_core_compressor_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=brushed_steel,
        name="compressor_stages",
    )
    core_rotor.visual(
        _save_mesh("core_turbine.obj", _rotate_engine_axis(_core_turbine_geometry())),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=heat_stained,
        name="turbine_stages",
    )
    core_rotor.inertial = Inertial.from_geometry(
        Cylinder(radius=0.170, length=0.800),
        mass=19.0,
        origin=Origin(xyz=(0.395, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    model.articulation(
        "fan_spin",
        ArticulationType.CONTINUOUS,
        parent="engine_case",
        child="fan_rotor",
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=120.0),
    )
    model.articulation(
        "engine_case_to_core_casing",
        ArticulationType.FIXED,
        parent="engine_case",
        child="core_casing",
        origin=Origin(xyz=(0.280, 0.0, 0.0)),
    )
    model.articulation(
        "core_spin",
        ArticulationType.CONTINUOUS,
        parent="core_casing",
        child="core_rotor",
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=55.0, velocity=260.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
