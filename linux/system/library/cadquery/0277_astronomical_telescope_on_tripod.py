# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from math import acos, atan2, cos, isfinite, pi, sin, sqrt, tan
from typing import Iterable, List, Optional, Sequence, Tuple, Union

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

# ===== primitives (1 syms) =====
class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

# ===== sweeps (24 syms) =====
Vec3 = Tuple[float, float, float]

def _v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def _v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def _v_scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)

def _v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def _v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def _v_norm(v):
    return sqrt(_v_dot(v, v))

def _v_normalize(v):
    n = _v_norm(v)
    if n <= _EPS:
        raise ValueError("Cannot normalize near-zero vector")
    return (v[0] / n, v[1] / n, v[2] / n)

def _v_rotate_rodrigues(v, axis, angle):
    k = _v_normalize(axis)
    c = cos(float(angle))
    s = sin(float(angle))
    term1 = _v_scale(v, c)
    term2 = _v_scale(_v_cross(k, v), s)
    term3 = _v_scale(k, _v_dot(k, v) * (1.0 - c))
    return _v_add(_v_add(term1, term2), term3)

def _sweeps_clamp(x, low, high):
    return max(low, min(high, x))

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

def sample_arc_3d(*, start_point, center, normal, angle, segments: int = 16):
    """Sample a circular 3D arc from ``start_point`` around (``center``, ``normal``)."""
    start = (float(start_point[0]), float(start_point[1]), float(start_point[2]))
    ctr = (float(center[0]), float(center[1]), float(center[2]))
    n = _v_normalize((float(normal[0]), float(normal[1]), float(normal[2])))
    steps = max(2, int(segments))

    radius_vec = _v_sub(start, ctr)
    axial = abs(_v_dot(_v_normalize(radius_vec), n)) if _v_norm(radius_vec) > _EPS else 1.0
    if _v_norm(radius_vec) <= _EPS or axial > 1.0 - 1e-6:
        raise ValueError("start_point must be away from center and not collinear with normal")

    out = []
    for i in range(steps + 1):
        t = float(i) / float(steps)
        rv = _v_rotate_rodrigues(radius_vec, n, float(angle) * t)
        out.append(_v_add(ctr, rv))
    return out

def _dedupe_path_points(path):
    if not path:
        return []
    out = [path[0]]
    for p in path[1:]:
        if _v_norm(_v_sub(p, out[-1])) > _EPS:
            out.append(p)
    return out

def _compute_path_tangents(path):
    n = len(path)
    if n < 2:
        raise ValueError("Pipe path requires at least two distinct points")
    tangents = []
    for i in range(n):
        if i == 0:
            d = _v_sub(path[1], path[0])
        elif i == n - 1:
            d = _v_sub(path[-1], path[-2])
        else:
            d = _v_sub(path[i + 1], path[i - 1])
        tangents.append(_v_normalize(d))
    return tangents

def _initial_frame(tangent, up_hint):
    up = _v_normalize(up_hint)
    if abs(_v_dot(up, tangent)) > 0.95:
        up = (0.0, 1.0, 0.0) if abs(tangent[1]) < 0.95 else (1.0, 0.0, 0.0)
    n = _v_cross(up, tangent)
    if _v_norm(n) <= _EPS:
        n = _v_cross((0.0, 0.0, 1.0), tangent)
    n = _v_normalize(n)
    b = _v_normalize(_v_cross(tangent, n))
    return (n, b)

@dataclass
class _WireCorner:
    incoming_end: Vec3
    outgoing_start: Vec3
    bridge: List[Vec3]

def _append_distinct_path_point(points, point, *, tol=_EPS):
    p = (float(point[0]), float(point[1]), float(point[2]))
    if not points or _v_norm(_v_sub(points[-1], p)) > tol:
        points.append(p)

def _preprocess_wire_polyline_points(points, *, min_segment_length, closed_path):
    raw = [(float(x), float(y), float(z)) for (x, y, z) in points]
    if len(raw) < 2:
        raise ValueError("WirePolylineGeometry requires at least two input points")

    tol = max(float(min_segment_length), _EPS)
    out = [raw[0]]
    for point in raw[1:]:
        if _v_norm(_v_sub(point, out[-1])) >= tol:
            out.append(point)

    if len(out) < 2:
        raise ValueError("Too few distinct points after dedupe")

    if closed_path:
        if _v_norm(_v_sub(out[0], out[-1])) <= tol:
            out[-1] = out[0]
        else:
            out.append(out[0])
        if len(out) < 4:
            raise ValueError("Closed path requires at least three distinct points")

    return out

def _wire_corner_from_three_points(prev_point, corner_point, next_point, *,
                                   corner_mode, corner_radius, corner_segments):
    incoming = _v_sub(corner_point, prev_point)
    outgoing = _v_sub(next_point, corner_point)
    len_in = _v_norm(incoming)
    len_out = _v_norm(outgoing)

    if len_in <= _EPS or len_out <= _EPS:
        if corner_mode == "fillet" and corner_radius > 0.0:
            raise ValueError("Impossible fillet: corner has zero-length segment")
        return _WireCorner(corner_point, corner_point, [corner_point])

    u = _v_scale(incoming, 1.0 / len_in)
    v = _v_scale(outgoing, 1.0 / len_out)
    theta = acos(_sweeps_clamp(_v_dot(_v_scale(u, -1.0), v), -1.0, 1.0))

    if theta <= 1e-6 or abs(pi - theta) <= 1e-6:
        return _WireCorner(corner_point, corner_point, [corner_point])
    if corner_mode == "miter" or corner_radius <= 0.0:
        return _WireCorner(corner_point, corner_point, [corner_point])

    tan_half = tan(theta * 0.5)
    if abs(tan_half) <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])

    target_trim = corner_radius * tan_half
    if not isfinite(target_trim):
        target_trim = float("inf")
    trim = min(target_trim, 0.49 * min(len_in, len_out))
    if trim <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])

    a = _v_sub(corner_point, _v_scale(u, trim))
    b = _v_add(corner_point, _v_scale(v, trim))

    if corner_mode == "bevel":
        return _WireCorner(a, b, [a, b])

    radius_eff = trim / tan_half
    if radius_eff <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])

    bisector = _v_add(_v_scale(u, -1.0), v)
    if _v_norm(bisector) <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])
    bisector = _v_normalize(bisector)

    sin_half = sin(theta * 0.5)
    if abs(sin_half) <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])
    center_dist = radius_eff / sin_half
    center = _v_add(corner_point, _v_scale(bisector, center_dist))

    axis = _v_cross(u, v)
    if _v_norm(axis) <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])
    axis = _v_normalize(axis)

    ra = _v_sub(a, center)
    rb = _v_sub(b, center)
    if _v_norm(ra) <= _EPS or _v_norm(rb) <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])
    ra_u = _v_normalize(ra)
    rb_u = _v_normalize(rb)

    arc_angle = acos(_sweeps_clamp(_v_dot(ra_u, rb_u), -1.0, 1.0))
    if _v_dot(axis, _v_cross(ra_u, rb_u)) < 0.0:
        arc_angle = -arc_angle
    if abs(arc_angle) <= _EPS:
        return _WireCorner(corner_point, corner_point, [corner_point])

    arc_points = sample_arc_3d(
        start_point=a, center=center, normal=axis, angle=arc_angle,
        segments=max(2, int(corner_segments)),
    )
    arc_points[0] = a
    arc_points[-1] = b
    return _WireCorner(a, b, arc_points)

def _build_wire_centerline(points, *, closed_path, corner_mode, corner_radius, corner_segments):
    if not closed_path:
        if len(points) < 2:
            raise ValueError("Wire path requires at least two points")
        if len(points) == 2:
            return list(points)

        out = []
        _append_distinct_path_point(out, points[0])
        for i in range(1, len(points) - 1):
            corner = _wire_corner_from_three_points(
                points[i - 1], points[i], points[i + 1],
                corner_mode=corner_mode, corner_radius=corner_radius, corner_segments=corner_segments,
            )
            _append_distinct_path_point(out, corner.incoming_end)
            for point in corner.bridge[1:]:
                _append_distinct_path_point(out, point)
        _append_distinct_path_point(out, points[-1])
        return out

    ring = points[:-1]
    if len(ring) < 3:
        raise ValueError("Closed path requires at least three distinct points")

    corners = []
    n = len(ring)
    for i in range(n):
        corners.append(
            _wire_corner_from_three_points(
                ring[(i - 1) % n], ring[i], ring[(i + 1) % n],
                corner_mode=corner_mode, corner_radius=corner_radius, corner_segments=corner_segments,
            )
        )

    out = []
    _append_distinct_path_point(out, corners[0].outgoing_start)
    for i in range(n):
        j = (i + 1) % n
        corner = corners[j]
        _append_distinct_path_point(out, corner.incoming_end)
        for point in corner.bridge[1:]:
            _append_distinct_path_point(out, point)
    if _v_norm(_v_sub(out[0], out[-1])) > _EPS:
        out.append(out[0])
    else:
        out[-1] = out[0]
    return out

def _wire_circle_profile(radius, radial_segments):
    return [
        (float(radius) * cos(2.0 * pi * i / radial_segments),
         float(radius) * sin(2.0 * pi * i / radial_segments))
        for i in range(radial_segments)
    ]

def _pipe_rings(profile, path, *, up_hint, path_closed, closed=True):
    """Transport a closed 2D profile along a 3D polyline using the same
    parallel-transport frames as the sdk PipeGeometry; return the list of
    3D cross-section rings (one closed loop of points per path station)."""
    raw_points = _profile_points_2d(profile)
    points = _ensure_ccw(raw_points) if closed else raw_points

    path_points = [(float(x), float(y), float(z)) for (x, y, z) in path]
    path_points = _dedupe_path_points(path_points)
    if len(path_points) < 2:
        raise ValueError("Pipe requires at least two distinct path points")
    if path_closed:
        if _v_norm(_v_sub(path_points[0], path_points[-1])) > _EPS:
            path_points.append(path_points[0])

    tangents = _compute_path_tangents(path_points)
    n0, b0 = _initial_frame(
        tangents[0], (float(up_hint[0]), float(up_hint[1]), float(up_hint[2]))
    )
    normals = [n0]
    binormals = [b0]
    for i in range(1, len(path_points)):
        t = tangents[i]
        prev_n = normals[-1]
        prev_b = binormals[-1]
        n = _v_sub(prev_n, _v_scale(t, _v_dot(prev_n, t)))
        if _v_norm(n) <= _EPS:
            n = _v_cross(prev_b, t)
        if _v_norm(n) <= _EPS:
            fallback = (0.0, 1.0, 0.0) if abs(t[1]) < 0.95 else (1.0, 0.0, 0.0)
            n = _v_cross(fallback, t)
        n = _v_normalize(n)
        b = _v_normalize(_v_cross(t, n))
        normals.append(n)
        binormals.append(b)
    if path_closed:
        normals[-1] = normals[0]
        binormals[-1] = binormals[0]

    rings = []
    for i, p in enumerate(path_points):
        n = normals[i]
        b = binormals[i]
        rings.append([
            (p[0] + x * n[0] + y * b[0], p[1] + x * n[1] + y * b[1], p[2] + x * n[2] + y * b[2])
            for (x, y) in points
        ])
    return rings

def _loft_section_solid(rings, *, ruled=True):
    """Ruled-loft a list of section rings (each a closed loop of 3D points)
    into a single capped cq.Solid. Ruled stitching reproduces the sdk's
    straight quad strips between adjacent rings exactly."""
    if len(rings) < 2:
        raise ValueError("loft requires at least two section rings")
    wires = [cq.Wire.makePolygon([cq.Vector(*p) for p in ring], close=True) for ring in rings]
    return cq.Solid.makeLoft(wires, ruled=bool(ruled))

def wire_from_points(points, *, radius, radial_segments: int = 16, closed_path: bool = False,
                     cap_ends: bool = False, corner_mode: str = "fillet", corner_radius: float = 0.0,
                     corner_segments: int = 8, up_hint=(0.0, 0.0, 1.0),
                     min_segment_length: float = 1e-6):
    """Build one circular tube/wire B-rep solid from a centerline path and radius.

    Corner handling (``fillet`` / ``miter`` / ``bevel``) matches the sdk
    WirePolylineGeometry centerline construction exactly; the swept circle is
    stitched into a parametric ruled loft instead of a triangle mesh."""
    radius = float(radius)
    radial_segments = int(radial_segments)
    closed_path = bool(closed_path)
    corner_mode = str(corner_mode).strip().lower()
    corner_radius = float(corner_radius)
    corner_segments = int(corner_segments)
    up_hint_v = (float(up_hint[0]), float(up_hint[1]), float(up_hint[2]))
    min_segment_length = float(min_segment_length)

    if radius <= 0.0:
        raise ValueError("radius must be > 0")
    if radial_segments < 6:
        raise ValueError("radial_segments must be >= 6")
    if corner_mode not in {"fillet", "miter", "bevel"}:
        raise ValueError("corner_mode must be one of: fillet, miter, bevel")
    if corner_radius < 0.0:
        raise ValueError("corner_radius must be >= 0")
    if corner_mode == "fillet" and corner_radius > 0.0 and corner_segments < 2:
        raise ValueError("corner_segments must be >= 2 when fillets are active")
    if _v_norm(up_hint_v) <= _EPS:
        raise ValueError("up_hint must be non-zero")
    if min_segment_length <= 0.0:
        raise ValueError("min_segment_length must be > 0")

    preprocessed = _preprocess_wire_polyline_points(
        points, min_segment_length=min_segment_length, closed_path=closed_path,
    )
    centerline = _build_wire_centerline(
        preprocessed, closed_path=closed_path, corner_mode=corner_mode,
        corner_radius=corner_radius, corner_segments=corner_segments,
    )
    centerline = _dedupe_path_points(centerline)
    if len(centerline) < 2:
        raise ValueError("Too few distinct points after corner preprocessing")

    profile = _wire_circle_profile(radius, radial_segments)
    rings = _pipe_rings(profile, centerline, up_hint=up_hint_v, path_closed=closed_path, closed=True)
    return MeshGeometry()._set(_loft_section_solid(rings, ruled=True))

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
DEFAULT_LATITUDE = math.radians(34.0)
def _rotate_pitch_yaw(
    vec: tuple[float, float, float],
    *,
    pitch: float,
    yaw: float,
) -> tuple[float, float, float]:
    x, y, z = vec
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)

    x_pitch = cp * x + sp * z
    z_pitch = -sp * x + cp * z

    return (
        cy * x_pitch - sy * y,
        sy * x_pitch + cy * y,
        z_pitch,
    )
def _tube_shell_mesh(
    name: str,
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
    flare: float = 0.0,
) -> object:
    half = length * 0.5
    outer = [
        (outer_radius + flare * 0.15, -half),
        (outer_radius + flare, -half + min(length * 0.12, 0.016)),
        (outer_radius, half - min(length * 0.08, 0.012)),
        (outer_radius, half),
    ]
    inner = [
        (inner_radius, -half + 0.0015),
        (inner_radius, half - 0.0015),
    ]
    return mesh_from_geometry(
        LatheGeometry.from_shell_profiles(
            outer,
            inner,
            segments=56,
            start_cap="flat",
            end_cap="flat",
        ),
        name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="astrograph_equatorial_wedge_mount")

    tripod_black = model.material("tripod_black", rgba=(0.12, 0.12, 0.13, 1.0))
    dark_gray = model.material("dark_gray", rgba=(0.22, 0.23, 0.25, 1.0))
    graphite = model.material("graphite", rgba=(0.18, 0.19, 0.21, 1.0))
    satin_silver = model.material("satin_silver", rgba=(0.67, 0.69, 0.72, 1.0))
    tube_white = model.material("tube_white", rgba=(0.92, 0.93, 0.95, 1.0))
    anodized_red = model.material("anodized_red", rgba=(0.56, 0.12, 0.12, 1.0))
    rubber_black = model.material("rubber_black", rgba=(0.08, 0.08, 0.09, 1.0))
    glass_blue = model.material("glass_blue", rgba=(0.53, 0.68, 0.82, 0.35))

    main_tube_mesh = _tube_shell_mesh(
        "astro_main_tube_shell",
        outer_radius=0.049,
        inner_radius=0.046,
        length=0.360,
    )
    dew_shield_mesh = _tube_shell_mesh(
        "astro_dew_shield_shell",
        outer_radius=0.058,
        inner_radius=0.055,
        length=0.140,
        flare=0.002,
    )
    tube_ring_mesh = mesh_from_geometry(
        TorusGeometry(radius=0.051, tube=0.006, radial_segments=16, tubular_segments=44),
        "astro_tube_ring",
    )
    belt_mesh = mesh_from_geometry(
        wire_from_points(
            [
                (-0.036, 0.074, 0.075),
                (0.000, 0.078, 0.075),
                (0.074, 0.000, 0.075),
                (0.000, -0.078, 0.075),
                (-0.036, -0.074, 0.075),
                (-0.108, -0.022, 0.075),
                (-0.134, 0.000, 0.075),
                (-0.108, 0.022, 0.075),
            ],
            radius=0.0023,
            closed_path=True,
            corner_mode="fillet",
            corner_radius=0.020,
            cap_ends=False,
        ),
        "astro_ra_belt",
    )

    tripod_hub = model.part("tripod_hub")
    tripod_hub.visual(
        Cylinder(radius=0.096, length=0.036),
        origin=Origin(xyz=(0.0, 0.0, 0.865)),
        material=tripod_black,
        name="crown",
    )
    tripod_hub.visual(
        Cylinder(radius=0.045, length=0.226),
        origin=Origin(xyz=(0.0, 0.0, 0.995)),
        material=dark_gray,
        name="center_column",
    )
    tripod_hub.visual(
        Cylinder(radius=0.055, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, 1.118)),
        material=graphite,
        name="pier_cap",
    )
    tripod_hub.inertial = Inertial.from_geometry(
        Box((0.26, 0.26, 0.30)),
        mass=4.8,
        origin=Origin(xyz=(0.0, 0.0, 1.000)),
    )

    wedge_base = model.part("wedge_base")
    wedge_base.visual(
        Box((0.190, 0.150, 0.018)),
        origin=Origin(xyz=(0.0, 0.0, 0.009)),
        material=dark_gray,
        name="base_plate",
    )
    wedge_base.visual(
        Box((0.120, 0.012, 0.092)),
        origin=Origin(xyz=(0.015, 0.056, 0.064)),
        material=graphite,
        name="left_cheek",
    )
    wedge_base.visual(
        Box((0.120, 0.012, 0.092)),
        origin=Origin(xyz=(0.015, -0.056, 0.064)),
        material=graphite,
        name="right_cheek",
    )
    wedge_base.visual(
        Box((0.050, 0.120, 0.040)),
        origin=Origin(xyz=(-0.055, 0.0, 0.020)),
        material=graphite,
        name="front_hinge_block",
    )
    wedge_base.visual(
        Box((0.034, 0.080, 0.022)),
        origin=Origin(xyz=(0.032, 0.0, 0.011)),
        material=graphite,
        name="rear_adjust_block",
    )
    wedge_base.visual(
        Cylinder(radius=0.008, length=0.074),
        origin=Origin(xyz=(0.044, 0.0, 0.018), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=satin_silver,
        name="latitude_adjust_screw",
    )
    wedge_base.inertial = Inertial.from_geometry(
        Box((0.190, 0.150, 0.110)),
        mass=2.6,
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
    )

    wedge_head = model.part("wedge_head")
    wedge_head.visual(
        Cylinder(radius=0.011, length=0.100),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=satin_silver,
        name="latitude_pivot_shaft",
    )
    wedge_head.visual(
        Box((0.060, 0.010, 0.090)),
        origin=Origin(xyz=(0.020, 0.037, 0.050)),
        material=dark_gray,
        name="left_head_arm",
    )
    wedge_head.visual(
        Box((0.060, 0.010, 0.090)),
        origin=Origin(xyz=(0.020, -0.037, 0.050)),
        material=dark_gray,
        name="right_head_arm",
    )
    wedge_head.visual(
        Box((0.220, 0.080, 0.010)),
        origin=Origin(xyz=(0.090, 0.0, 0.088)),
        material=satin_silver,
        name="tilt_plate",
    )
    wedge_head.visual(
        Box((0.110, 0.090, 0.018)),
        origin=Origin(xyz=(0.108, 0.0, 0.079)),
        material=graphite,
        name="polar_spine",
    )
    wedge_head.visual(
        Box((0.050, 0.060, 0.018)),
        origin=Origin(xyz=(0.172, 0.0, 0.079)),
        material=graphite,
        name="rear_stiffener",
    )
    wedge_head.inertial = Inertial.from_geometry(
        Box((0.250, 0.120, 0.100)),
        mass=1.9,
        origin=Origin(xyz=(0.090, 0.0, 0.040)),
    )

    ra_assembly = model.part("ra_assembly")
    ra_assembly.visual(
        Cylinder(radius=0.055, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
        material=graphite,
        name="ra_flange",
    )
    ra_assembly.visual(
        Cylinder(radius=0.046, length=0.220),
        origin=Origin(xyz=(0.0, 0.0, 0.124)),
        material=satin_silver,
        name="ra_housing",
    )
    ra_assembly.visual(
        Cylinder(radius=0.074, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.075)),
        material=anodized_red,
        name="drive_pulley",
    )
    ra_assembly.visual(
        Box((0.080, 0.030, 0.030)),
        origin=Origin(xyz=(-0.055, 0.0, 0.070)),
        material=graphite,
        name="motor_bridge",
    )
    ra_assembly.visual(
        Box((0.070, 0.050, 0.060)),
        origin=Origin(xyz=(-0.108, 0.0, 0.062)),
        material=dark_gray,
        name="motor_housing",
    )
    ra_assembly.visual(
        Cylinder(radius=0.022, length=0.010),
        origin=Origin(xyz=(-0.108, 0.0, 0.075)),
        material=anodized_red,
        name="motor_pulley",
    )
    ra_assembly.visual(
        belt_mesh,
        material=rubber_black,
        name="drive_belt",
    )
    ra_assembly.visual(
        Box((0.070, 0.060, 0.130)),
        origin=Origin(xyz=(0.055, 0.0, 0.210)),
        material=dark_gray,
        name="saddle_tower",
    )
    ra_assembly.visual(
        Box((0.180, 0.036, 0.012)),
        origin=Origin(xyz=(0.120, 0.0, 0.281)),
        material=satin_silver,
        name="saddle_base",
    )
    ra_assembly.visual(
        Box((0.180, 0.006, 0.030)),
        origin=Origin(xyz=(0.120, 0.019, 0.302)),
        material=graphite,
        name="saddle_wall_pos",
    )
    ra_assembly.visual(
        Box((0.180, 0.006, 0.030)),
        origin=Origin(xyz=(0.120, -0.019, 0.302)),
        material=graphite,
        name="saddle_wall_neg",
    )
    ra_assembly.visual(
        Cylinder(radius=0.038, length=0.045),
        origin=Origin(xyz=(0.0, 0.0, 0.245)),
        material=graphite,
        name="upper_bearing_cap",
    )
    ra_assembly.inertial = Inertial.from_geometry(
        Box((0.280, 0.120, 0.330)),
        mass=3.0,
        origin=Origin(xyz=(0.030, 0.0, 0.165)),
    )

    optical_tube = model.part("optical_tube")
    optical_tube.visual(
        Box((0.360, 0.032, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=satin_silver,
        name="dovetail_bar",
    )
    for index, ring_x in enumerate((-0.140, 0.125)):
        optical_tube.visual(
            Box((0.026, 0.028, 0.044)),
            origin=Origin(xyz=(ring_x, 0.0, 0.032)),
            material=anodized_red,
            name=f"ring_block_{index}",
        )
        optical_tube.visual(
            tube_ring_mesh,
            origin=Origin(xyz=(ring_x, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=anodized_red,
            name=f"tube_ring_{index}",
        )
    optical_tube.visual(
        main_tube_mesh,
        origin=Origin(xyz=(0.010, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=tube_white,
        name="main_tube_shell",
    )
    optical_tube.visual(
        dew_shield_mesh,
        origin=Origin(xyz=(-0.240, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="dew_shield_shell",
    )
    optical_tube.visual(
        Cylinder(radius=0.056, length=0.020),
        origin=Origin(xyz=(-0.175, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="dew_shield_adapter",
    )
    optical_tube.visual(
        Cylinder(radius=0.053, length=0.012),
        origin=Origin(xyz=(-0.168, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="dew_shield_collar",
    )
    optical_tube.visual(
        Cylinder(radius=0.052, length=0.020),
        origin=Origin(xyz=(-0.180, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="dew_shield_joiner",
    )
    optical_tube.visual(
        Cylinder(radius=0.058, length=0.020),
        origin=Origin(xyz=(-0.304, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="objective_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.057, length=0.002),
        origin=Origin(xyz=(-0.313, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass_blue,
        name="objective_glass",
    )
    optical_tube.visual(
        Cylinder(radius=0.049, length=0.016),
        origin=Origin(xyz=(0.198, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="rear_adapter",
    )
    optical_tube.visual(
        Cylinder(radius=0.038, length=0.094),
        origin=Origin(xyz=(0.253, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="focuser_body",
    )
    optical_tube.visual(
        Cylinder(radius=0.029, length=0.090),
        origin=Origin(xyz=(0.345, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=satin_silver,
        name="drawtube",
    )
    optical_tube.visual(
        Cylinder(radius=0.042, length=0.082),
        origin=Origin(xyz=(0.431, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="imaging_camera",
    )
    optical_tube.visual(
        Cylinder(radius=0.032, length=0.012),
        origin=Origin(xyz=(0.478, 0.0, 0.078), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=anodized_red,
        name="camera_nosepiece",
    )
    optical_tube.visual(
        Cylinder(radius=0.010, length=0.014),
        origin=Origin(xyz=(0.250, 0.040, 0.060), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=graphite,
        name="focuser_knob_left",
    )
    optical_tube.visual(
        Cylinder(radius=0.010, length=0.014),
        origin=Origin(xyz=(0.250, -0.040, 0.060), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=graphite,
        name="focuser_knob_right",
    )
    optical_tube.visual(
        Box((0.050, 0.020, 0.010)),
        origin=Origin(xyz=(0.000, 0.0, 0.132)),
        material=graphite,
        name="finder_shoe",
    )
    optical_tube.inertial = Inertial.from_geometry(
        Box((0.800, 0.140, 0.150)),
        mass=3.3,
        origin=Origin(xyz=(0.080, 0.0, 0.078)),
    )

    saddle_knob = model.part("saddle_knob")
    saddle_knob.visual(
        Cylinder(radius=0.006, length=0.010),
        origin=Origin(xyz=(0.0, 0.005, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=satin_silver,
        name="knob_hub",
    )
    saddle_knob.visual(
        Cylinder(radius=0.012, length=0.010),
        origin=Origin(xyz=(0.0, 0.015, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=graphite,
        name="knob_body",
    )
    saddle_knob.visual(
        Cylinder(radius=0.004, length=0.035),
        origin=Origin(xyz=(0.012, 0.015, 0.0)),
        material=graphite,
        name="knob_handle",
    )
    saddle_knob.inertial = Inertial.from_geometry(
        Box((0.045, 0.032, 0.035)),
        mass=0.08,
        origin=Origin(xyz=(0.010, 0.016, 0.0)),
    )

    model.articulation(
        "tripod_to_wedge_base",
        ArticulationType.FIXED,
        parent=tripod_hub,
        child=wedge_base,
        origin=Origin(xyz=(0.0, 0.0, 1.128)),
    )
    model.articulation(
        "wedge_latitude",
        ArticulationType.REVOLUTE,
        parent=wedge_base,
        child=wedge_head,
        origin=Origin(
            xyz=(-0.030, 0.0, 0.053),
            rpy=(0.0, DEFAULT_LATITUDE, 0.0),
        ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=0.30,
            lower=-math.radians(12.0),
            upper=math.radians(18.0),
        ),
    )
    model.articulation(
        "wedge_to_ra",
        ArticulationType.CONTINUOUS,
        parent=wedge_head,
        child=ra_assembly,
        origin=Origin(xyz=(0.155, 0.0, 0.065)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5),
    )
    model.articulation(
        "ra_to_optical_tube",
        ArticulationType.FIXED,
        parent=ra_assembly,
        child=optical_tube,
        origin=Origin(xyz=(0.120, 0.0, 0.293)),
    )
    model.articulation(
        "saddle_knob_spin",
        ArticulationType.REVOLUTE,
        parent=ra_assembly,
        child=saddle_knob,
        origin=Origin(xyz=(0.155, 0.022, 0.304)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.5,
            velocity=3.0,
            lower=-1.2,
            upper=1.2,
        ),
    )

    leg_specs = [
        ("front", 0.0),
        ("left", 2.0 * math.pi / 3.0),
        ("right", 4.0 * math.pi / 3.0),
    ]
    hip_radius = 0.074
    hip_z = 0.852
    upper_length = 0.460
    lower_length = 0.540
    outer_x = 0.032
    outer_y = 0.018
    wall = 0.0035
    leg_pitch = -math.radians(23.0)

    for leg_name, yaw in leg_specs:
        hip_point = (hip_radius * math.cos(yaw), hip_radius * math.sin(yaw), hip_z)
        leg_rpy = (0.0, leg_pitch, yaw)
        socket_offset = _rotate_pitch_yaw((0.0, 0.0, -0.010), pitch=leg_pitch, yaw=yaw)
        tripod_hub.visual(
            Box((0.054, 0.034, 0.020)),
            origin=Origin(
                xyz=(
                    hip_point[0] + socket_offset[0],
                    hip_point[1] + socket_offset[1],
                    hip_point[2] + socket_offset[2],
                ),
                rpy=leg_rpy,
            ),
            material=graphite,
            name=f"{leg_name}_socket",
        )

        upper_leg = model.part(f"upper_leg_{leg_name}")
        upper_leg.visual(
            Box((outer_x, outer_y, 0.020)),
            origin=Origin(xyz=(0.0, 0.0, -0.030)),
            material=graphite,
            name="top_shoe",
        )
        upper_leg.visual(
            Box((wall, outer_y, upper_length)),
            origin=Origin(xyz=(outer_x * 0.5 - wall * 0.5, 0.0, -0.260)),
            material=tripod_black,
            name="rail_pos_x",
        )
        upper_leg.visual(
            Box((wall, outer_y, upper_length)),
            origin=Origin(xyz=(-(outer_x * 0.5 - wall * 0.5), 0.0, -0.260)),
            material=tripod_black,
            name="rail_neg_x",
        )
        upper_leg.visual(
            Box((outer_x - 2.0 * wall, wall, upper_length)),
            origin=Origin(xyz=(0.0, outer_y * 0.5 - wall * 0.5, -0.260)),
            material=tripod_black,
            name="rail_pos_y",
        )
        upper_leg.visual(
            Box((outer_x - 2.0 * wall, wall, upper_length)),
            origin=Origin(xyz=(0.0, -(outer_y * 0.5 - wall * 0.5), -0.260)),
            material=tripod_black,
            name="rail_neg_y",
        )
        upper_leg.inertial = Inertial.from_geometry(
            Box((0.054, 0.034, 0.500)),
            mass=0.85,
            origin=Origin(xyz=(0.0, 0.0, -0.250)),
        )

        lower_leg = model.part(f"lower_leg_{leg_name}")
        lower_leg.visual(
            Box((0.018, 0.011, 0.546)),
            origin=Origin(xyz=(0.0, 0.0, -0.262)),
            material=satin_silver,
            name="inner_tube",
        )
        lower_leg.visual(
            Box((0.012, 0.004, 0.008)),
            origin=Origin(xyz=(0.0, 0.0, 0.0017)),
            material=graphite,
            name="top_stop",
        )
        lower_leg.visual(
            Box((0.050, 0.024, 0.016)),
            origin=Origin(xyz=(0.0, 0.0, -0.543)),
            material=rubber_black,
            name="foot_pad",
        )
        lower_leg.inertial = Inertial.from_geometry(
            Box((0.050, 0.024, 0.560)),
            mass=0.55,
            origin=Origin(xyz=(0.0, 0.0, -0.280)),
        )

        model.articulation(
            f"tripod_to_upper_leg_{leg_name}",
            ArticulationType.FIXED,
            parent=tripod_hub,
            child=upper_leg,
            origin=Origin(xyz=hip_point, rpy=leg_rpy),
        )
        model.articulation(
            f"upper_to_lower_leg_{leg_name}",
            ArticulationType.PRISMATIC,
            parent=upper_leg,
            child=lower_leg,
            origin=Origin(xyz=(0.0, 0.0, -0.055)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=14.0,
                velocity=0.08,
                lower=0.0,
                upper=0.220,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
