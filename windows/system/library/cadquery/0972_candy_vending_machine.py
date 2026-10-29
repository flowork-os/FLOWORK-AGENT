# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, candy_vending_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: candy_vending_machine

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

# ===== brackets_hinges_bezels (1 syms) =====
_EPS = 1e-9

# ===== primitives (1 syms) =====
class CylinderGeometry(MeshGeometry):
    def __init__(self, radius, height, *, radial_segments=24, closed=True):
        super().__init__()
        radius = float(radius)
        height = float(height)
        solid = cq.Solid.makeCylinder(
            radius, height, cq.Vector(0, 0, -height / 2.0), cq.Vector(0, 0, 1)
        )
        self._set(solid)

# ===== sweeps (33 syms) =====
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

def sample_cubic_bezier_spline_3d(control_points, *, samples_per_segment: int = 12):
    """Sample a C1-continuous chained cubic Bezier spline in 3D."""
    pts = [(float(x), float(y), float(z)) for (x, y, z) in control_points]
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
        z = b0 * p0[2] + b1 * p1[2] + b2 * p2[2] + b3 * p3[2]
        return (x, y, z)

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

def sample_catmull_rom_spline_3d(points, *, samples_per_segment: int = 12,
                                 closed: bool = False, alpha: float = 0.5):
    """Sample a centripetal Catmull-Rom spline through the input 3D points."""
    sampled = _sample_catmull_rom_spline(
        points, samples_per_segment=samples_per_segment, closed=bool(closed), alpha=float(alpha),
    )
    return [(float(x), float(y), float(z)) for (x, y, z) in sampled]

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

def _sample_supported_spline_path(points, *, spline, samples_per_segment, closed_spline,
                                  alpha, min_segment_length):
    spline_key = str(spline or "catmull_rom").strip().lower().replace("-", "_")
    if spline_key in {"catmullrom", "catmull_rom"}:
        sampled = sample_catmull_rom_spline_3d(
            list(points), samples_per_segment=int(samples_per_segment),
            closed=bool(closed_spline), alpha=float(alpha),
        )
    elif spline_key in {"bezier", "cubic_bezier", "cubicbezier"}:
        sampled = sample_cubic_bezier_spline_3d(
            list(points), samples_per_segment=int(samples_per_segment),
        )
        if bool(closed_spline) and _v_norm(_v_sub(sampled[0], sampled[-1])) > max(
            float(min_segment_length), _EPS
        ):
            raise ValueError(
                "closed_spline=True with spline='bezier' requires the sampled "
                "Bezier chain to end where it starts"
            )
    else:
        raise ValueError("spline must be one of: 'catmull_rom', 'bezier'")

    return _preprocess_wire_polyline_points(
        sampled, min_segment_length=float(min_segment_length), closed_path=bool(closed_spline),
    )

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

def tube_from_spline_points(points, *, radius, samples_per_segment: int = 12,
                            closed_spline: bool = False, spline: str = "catmull_rom",
                            alpha: float = 0.5, radial_segments: int = 16, cap_ends: bool = True,
                            up_hint=(0.0, 0.0, 1.0), min_segment_length: float = 1e-6):
    """Fit a spline (``catmull_rom`` or chained ``bezier``) through the points,
    then build a circular tube B-rep along that path."""
    centerline = _sample_supported_spline_path(
        points, spline=spline, samples_per_segment=samples_per_segment,
        closed_spline=closed_spline, alpha=alpha, min_segment_length=min_segment_length,
    )
    return wire_from_points(
        centerline, radius=float(radius), radial_segments=int(radial_segments),
        closed_path=bool(closed_spline), cap_ends=bool(cap_ends), corner_mode="miter",
        up_hint=up_hint, min_segment_length=min_segment_length,
    )

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
BODY_WIDTH = 0.46
BODY_DEPTH = 0.38
BODY_HEIGHT = 1.58
WALL = 0.02
FRONT_Y = BODY_DEPTH * 0.5 - WALL * 0.5
def _coil_mesh(name: str, *, radius: float, length: float, wire_radius: float, turns: float):
    samples = max(72, int(turns * 30))
    points = []
    for i in range(samples + 1):
        t = i / samples
        angle = turns * 2.0 * pi * t
        points.append(
            (
                radius * cos(angle),
                -length * 0.5 + length * t,
                radius * sin(angle),
            )
        )

    coil_geom = tube_from_spline_points(
        points,
        radius=wire_radius,
        samples_per_segment=1,
        radial_segments=16,
        cap_ends=True,
        up_hint=(0.0, 0.0, 1.0),
    )
    shaft_radius = wire_radius * 1.45
    shaft_geom = CylinderGeometry(shaft_radius, length + 0.03, radial_segments=18, closed=True).rotate_x(-pi / 2.0)
    rear_spoke = tube_from_spline_points(
        [(shaft_radius, -length * 0.5, 0.0), (radius * 0.98, -length * 0.5, 0.0)],
        radius=wire_radius * 0.72,
        samples_per_segment=1,
        radial_segments=12,
        cap_ends=True,
    )
    front_spoke = tube_from_spline_points(
        [(shaft_radius, length * 0.5, 0.0), (radius * 0.98, length * 0.5, 0.0)],
        radius=wire_radius * 0.72,
        samples_per_segment=1,
        radial_segments=12,
        cap_ends=True,
    )
    coil_geom.merge(shaft_geom)
    coil_geom.merge(rear_spoke)
    coil_geom.merge(front_spoke)
    return mesh_from_geometry(coil_geom, name)
def _add_spiral_stage(
    model: ArticulatedObject,
    *,
    name: str,
    mount_xyz: tuple[float, float, float],
    steel,
    tray_gray,
    candy_color,
) -> None:
    tray_width = 0.275
    tray_depth = 0.236
    tray_thickness = 0.006
    rail_thickness = 0.006
    rail_height = 0.020
    support_width = 0.030
    support_depth = 0.012
    support_height = 0.060
    coil_length = 0.206
    coil_radius = 0.044
    coil_wire = 0.0052

    stage = model.part(name)
    stage.visual(
        Box((tray_width, tray_depth, tray_thickness)),
        origin=Origin(xyz=(0.0, 0.0, -0.058)),
        material=tray_gray,
        name="tray_floor",
    )
    stage.visual(
        Box((tray_width, rail_thickness, 0.024)),
        origin=Origin(xyz=(0.0, tray_depth * 0.5 - rail_thickness * 0.5, -0.046)),
        material=tray_gray,
        name="front_lip",
    )
    stage.visual(
        Box((tray_width, rail_thickness, 0.028)),
        origin=Origin(xyz=(0.0, -tray_depth * 0.5 + rail_thickness * 0.5, -0.044)),
        material=tray_gray,
        name="rear_lip",
    )
    stage.visual(
        Box((rail_thickness, tray_depth, rail_height)),
        origin=Origin(xyz=(-tray_width * 0.5 + rail_thickness * 0.5, 0.0, -0.046)),
        material=tray_gray,
        name="left_rail",
    )
    stage.visual(
        Box((rail_thickness, tray_depth, rail_height)),
        origin=Origin(xyz=(tray_width * 0.5 - rail_thickness * 0.5, 0.0, -0.046)),
        material=tray_gray,
        name="right_rail",
    )
    stage.visual(
        Box((support_width, support_depth, support_height)),
        origin=Origin(xyz=(0.0, -coil_length * 0.5 - 0.010, -0.028)),
        material=tray_gray,
        name="rear_support",
    )
    stage.visual(
        Box((support_width, support_depth, support_height)),
        origin=Origin(xyz=(0.0, coil_length * 0.5 + 0.010, -0.028)),
        material=tray_gray,
        name="front_support",
    )
    stage.visual(
        _coil_mesh(
            f"{name}_coil",
            radius=coil_radius,
            length=coil_length,
            wire_radius=coil_wire,
            turns=3.7,
        ),
        material=steel,
        name="spiral_assembly",
    )
    stage.visual(
        Box((0.042, 0.028, 0.020)),
        origin=Origin(xyz=(-0.078, -0.070, -0.046)),
        material=candy_color,
        name="candy_box_left",
    )
    stage.visual(
        Box((0.040, 0.026, 0.018)),
        origin=Origin(xyz=(0.012, 0.000, -0.047)),
        material=candy_color,
        name="candy_box_mid",
    )
    stage.visual(
        Box((0.040, 0.028, 0.018)),
        origin=Origin(xyz=(0.086, 0.070, -0.046)),
        material=candy_color,
        name="candy_box_right",
    )
    stage.inertial = Inertial.from_geometry(
        Box((tray_width, tray_depth, 0.130)),
        mass=1.1,
        origin=Origin(xyz=(0.0, 0.0, -0.030)),
    )

    model.articulation(
        f"{name}_mount",
        ArticulationType.FIXED,
        parent="cabinet",
        child=stage,
        origin=Origin(xyz=mount_xyz),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_candy_vending_machine")

    cabinet_red = model.material("cabinet_red", rgba=(0.73, 0.12, 0.12, 1.0))
    trim_black = model.material("trim_black", rgba=(0.10, 0.11, 0.12, 1.0))
    steel = model.material("steel", rgba=(0.73, 0.75, 0.78, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.35, 0.36, 0.38, 1.0))
    tray_gray = model.material("tray_gray", rgba=(0.44, 0.45, 0.48, 1.0))
    smoked_glass = model.material("smoked_glass", rgba=(0.60, 0.82, 0.93, 0.26))
    panel_black = model.material("panel_black", rgba=(0.12, 0.13, 0.14, 1.0))
    lcd_green = model.material("lcd_green", rgba=(0.24, 0.42, 0.26, 1.0))
    button_red = model.material("button_red", rgba=(0.78, 0.16, 0.14, 1.0))
    button_yellow = model.material("button_yellow", rgba=(0.88, 0.71, 0.18, 1.0))
    candy_cyan = model.material("candy_cyan", rgba=(0.18, 0.72, 0.84, 1.0))
    candy_magenta = model.material("candy_magenta", rgba=(0.80, 0.31, 0.56, 1.0))
    candy_orange = model.material("candy_orange", rgba=(0.92, 0.49, 0.16, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        Box((BODY_WIDTH, 0.090, 0.10)),
        origin=Origin(xyz=(0.0, -0.145, 0.05)),
        material=trim_black,
        name="base_plinth",
    )
    cabinet.visual(
        Box((0.030, 0.240, 0.10)),
        origin=Origin(xyz=(-0.215, -0.070, 0.05)),
        material=trim_black,
        name="left_base_leg",
    )
    cabinet.visual(
        Box((0.030, 0.240, 0.10)),
        origin=Origin(xyz=(0.215, -0.070, 0.05)),
        material=trim_black,
        name="right_base_leg",
    )
    cabinet.visual(
        Box((BODY_WIDTH, WALL, BODY_HEIGHT - 0.10)),
        origin=Origin(xyz=(0.0, -BODY_DEPTH * 0.5 + WALL * 0.5, 0.84)),
        material=cabinet_red,
        name="back_panel",
    )
    cabinet.visual(
        Box((WALL, BODY_DEPTH, BODY_HEIGHT - 0.10)),
        origin=Origin(xyz=(-BODY_WIDTH * 0.5 + WALL * 0.5, 0.0, 0.84)),
        material=cabinet_red,
        name="left_side",
    )
    cabinet.visual(
        Box((WALL, BODY_DEPTH, BODY_HEIGHT - 0.10)),
        origin=Origin(xyz=(BODY_WIDTH * 0.5 - WALL * 0.5, 0.0, 0.84)),
        material=cabinet_red,
        name="right_side",
    )
    cabinet.visual(
        Box((BODY_WIDTH, BODY_DEPTH, WALL)),
        origin=Origin(xyz=(0.0, 0.0, BODY_HEIGHT - WALL * 0.5)),
        material=cabinet_red,
        name="roof_panel",
    )
    cabinet.visual(
        Box((WALL, BODY_DEPTH - 0.04, 1.04)),
        origin=Origin(xyz=(0.085, -0.01, 1.05)),
        material=trim_black,
        name="bay_divider",
    )
    cabinet.visual(
        Box((0.025, 0.024, 0.94)),
        origin=Origin(xyz=(-0.207, FRONT_Y, 1.00)),
        material=trim_black,
        name="glass_left_frame",
    )
    cabinet.visual(
        Box((0.025, 0.024, 0.94)),
        origin=Origin(xyz=(0.072, FRONT_Y, 1.00)),
        material=trim_black,
        name="glass_right_frame",
    )
    cabinet.visual(
        Box((0.304, 0.024, 0.025)),
        origin=Origin(xyz=(-0.067, FRONT_Y, 1.457)),
        material=trim_black,
        name="glass_top_frame",
    )
    cabinet.visual(
        Box((0.304, 0.024, 0.025)),
        origin=Origin(xyz=(-0.067, FRONT_Y, 0.542)),
        material=trim_black,
        name="glass_bottom_frame",
    )
    cabinet.visual(
        Box((0.118, 0.024, 1.02)),
        origin=Origin(xyz=(0.151, FRONT_Y, 0.965)),
        material=trim_black,
        name="control_column_front",
    )
    cabinet.visual(
        Box((0.420, 0.024, 0.026)),
        origin=Origin(xyz=(0.0, FRONT_Y, 0.172)),
        material=trim_black,
        name="drawer_header",
    )
    cabinet.visual(
        Box((0.252, 0.024, 0.026)),
        origin=Origin(xyz=(-0.070, FRONT_Y, 0.198)),
        material=trim_black,
        name="pickup_sill",
    )
    cabinet.visual(
        Box((0.252, 0.024, 0.026)),
        origin=Origin(xyz=(-0.070, FRONT_Y, 0.328)),
        material=trim_black,
        name="pickup_header",
    )
    cabinet.visual(
        Box((0.026, 0.024, 0.124)),
        origin=Origin(xyz=(-0.196, FRONT_Y, 0.266)),
        material=trim_black,
        name="pickup_left_jamb",
    )
    cabinet.visual(
        Box((0.026, 0.024, 0.124)),
        origin=Origin(xyz=(0.056, FRONT_Y, 0.266)),
        material=trim_black,
        name="pickup_right_jamb",
    )
    cabinet.visual(
        Box((0.252, 0.024, 0.190)),
        origin=Origin(xyz=(-0.070, FRONT_Y, 0.435)),
        material=cabinet_red,
        name="front_mid_panel",
    )
    cabinet.visual(
        Box((0.222, 0.190, 0.018)),
        origin=Origin(xyz=(-0.070, 0.085, 0.192)),
        material=tray_gray,
        name="pickup_chute_floor",
    )
    cabinet.visual(
        Box((0.220, 0.018, 0.108)),
        origin=Origin(xyz=(-0.070, 0.004, 0.255)),
        material=tray_gray,
        name="pickup_chute_back",
    )
    cabinet.visual(
        Box((0.018, 0.256, 0.010)),
        origin=Origin(xyz=(-0.160, -0.012, 0.102)),
        material=dark_steel,
        name="left_runner",
    )
    cabinet.visual(
        Box((0.018, 0.256, 0.010)),
        origin=Origin(xyz=(0.160, -0.012, 0.102)),
        material=dark_steel,
        name="right_runner",
    )
    cabinet.visual(
        Box((0.280, 0.060, 0.050)),
        origin=Origin(xyz=(-0.067, 0.105, 1.535)),
        material=steel,
        name="top_light_baffle",
    )
    cabinet.inertial = Inertial.from_geometry(
        Box((BODY_WIDTH, BODY_DEPTH, BODY_HEIGHT)),
        mass=68.0,
        origin=Origin(xyz=(0.0, 0.0, BODY_HEIGHT * 0.5)),
    )

    glass = model.part("glass_front")
    glass.visual(
        Box((0.276, 0.008, 0.882)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=smoked_glass,
        name="glass_panel",
    )
    glass.inertial = Inertial.from_geometry(Box((0.276, 0.008, 0.882)), mass=3.0)
    model.articulation(
        "cabinet_to_glass",
        ArticulationType.FIXED,
        parent=cabinet,
        child=glass,
        origin=Origin(xyz=(-0.067, 0.164, 0.995)),
    )

    control_panel = model.part("control_panel")
    control_panel.visual(
        Box((0.110, 0.032, 0.292)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=panel_black,
        name="panel_housing",
    )
    control_panel.visual(
        Box((0.090, 0.006, 0.270)),
        origin=Origin(xyz=(0.0, 0.019, 0.0)),
        material=trim_black,
        name="panel_face",
    )
    control_panel.visual(
        Box((0.060, 0.004, 0.038)),
        origin=Origin(xyz=(0.0, 0.022, 0.094)),
        material=lcd_green,
        name="display_window",
    )
    control_panel.visual(
        Box((0.042, 0.014, 0.006)),
        origin=Origin(xyz=(0.0, 0.017, 0.146)),
        material=dark_steel,
        name="coin_slot",
    )
    control_panel.visual(
        Cylinder(radius=0.010, length=0.012),
        origin=Origin(xyz=(-0.028, 0.022, -0.096), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=button_red,
        name="cancel_button",
    )
    control_panel.visual(
        Cylinder(radius=0.010, length=0.012),
        origin=Origin(xyz=(0.028, 0.022, -0.096), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=button_yellow,
        name="vend_button",
    )
    control_panel.visual(
        Box((0.050, 0.004, 0.020)),
        origin=Origin(xyz=(0.0, 0.022, -0.142)),
        material=dark_steel,
        name="return_tray",
    )
    control_panel.inertial = Inertial.from_geometry(
        Box((0.110, 0.032, 0.292)),
        mass=1.4,
        origin=Origin(),
    )
    model.articulation(
        "cabinet_to_control_panel",
        ArticulationType.FIXED,
        parent=cabinet,
        child=control_panel,
        origin=Origin(xyz=(0.151, 0.208, 0.868)),
    )

    dial = model.part("selector_dial")
    dial.visual(
        Cylinder(radius=0.036, length=0.022),
        origin=Origin(xyz=(0.0, 0.011, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="dial_knob",
    )
    dial.visual(
        Cylinder(radius=0.028, length=0.010),
        origin=Origin(xyz=(0.0, 0.006, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="dial_face",
    )
    dial.visual(
        Box((0.008, 0.006, 0.026)),
        origin=Origin(xyz=(0.0, 0.024, 0.024)),
        material=button_red,
        name="dial_pointer",
    )
    dial.inertial = Inertial.from_geometry(
        Box((0.072, 0.032, 0.072)),
        mass=0.25,
        origin=Origin(xyz=(0.0, 0.016, 0.0)),
    )
    model.articulation(
        "control_panel_to_selector_dial",
        ArticulationType.CONTINUOUS,
        parent=control_panel,
        child=dial,
        origin=Origin(xyz=(0.0, 0.019, -0.008)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.2, velocity=6.0),
    )

    drawer = model.part("cash_drawer")
    drawer.visual(
        Box((0.292, 0.224, 0.036)),
        origin=Origin(xyz=(0.0, 0.0, 0.036)),
        material=tray_gray,
        name="drawer_body",
    )
    drawer.visual(
        Box((0.010, 0.224, 0.050)),
        origin=Origin(xyz=(-0.141, 0.0, 0.053)),
        material=tray_gray,
        name="left_bin_wall",
    )
    drawer.visual(
        Box((0.010, 0.224, 0.050)),
        origin=Origin(xyz=(0.141, 0.0, 0.053)),
        material=tray_gray,
        name="right_bin_wall",
    )
    drawer.visual(
        Box((0.272, 0.010, 0.050)),
        origin=Origin(xyz=(0.0, -0.107, 0.053)),
        material=tray_gray,
        name="rear_bin_wall",
    )
    drawer.visual(
        Box((0.008, 0.140, 0.035)),
        origin=Origin(xyz=(0.0, -0.010, 0.045)),
        material=dark_steel,
        name="cash_divider",
    )
    drawer.visual(
        Box((0.394, 0.024, 0.124)),
        origin=Origin(xyz=(0.0, 0.122, 0.002)),
        material=dark_steel,
        name="drawer_face",
    )
    drawer.visual(
        Box((0.112, 0.018, 0.020)),
        origin=Origin(xyz=(0.0, 0.142, 0.006)),
        material=steel,
        name="drawer_handle",
    )
    drawer.visual(
        Box((0.010, 0.178, 0.004)),
        origin=Origin(xyz=(-0.160, -0.012, 0.013)),
        material=dark_steel,
        name="left_tongue",
    )
    drawer.visual(
        Box((0.010, 0.178, 0.004)),
        origin=Origin(xyz=(0.160, -0.012, 0.013)),
        material=dark_steel,
        name="right_tongue",
    )
    drawer.visual(
        Box((0.020, 0.178, 0.020)),
        origin=Origin(xyz=(-0.150, -0.012, 0.023)),
        material=dark_steel,
        name="left_slide_bracket",
    )
    drawer.visual(
        Box((0.020, 0.178, 0.020)),
        origin=Origin(xyz=(0.150, -0.012, 0.023)),
        material=dark_steel,
        name="right_slide_bracket",
    )
    drawer.inertial = Inertial.from_geometry(
        Box((0.404, 0.244, 0.124)),
        mass=3.0,
        origin=Origin(xyz=(0.0, 0.012, 0.002)),
    )
    model.articulation(
        "cabinet_to_cash_drawer",
        ArticulationType.PRISMATIC,
        parent=cabinet,
        child=drawer,
        origin=Origin(xyz=(0.0, 0.038, 0.090)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=40.0, velocity=0.35, lower=0.0, upper=0.130),
    )

    flap = model.part("retrieval_flap")
    flap.visual(
        Box((0.228, 0.012, 0.110)),
        origin=Origin(xyz=(0.0, 0.006, -0.055)),
        material=panel_black,
        name="flap_panel",
    )
    flap.visual(
        Cylinder(radius=0.007, length=0.232),
        origin=Origin(xyz=(0.0, 0.007, 0.000), rpy=(0.0, pi / 2.0, 0.0)),
        material=dark_steel,
        name="hinge_barrel",
    )
    flap.inertial = Inertial.from_geometry(
        Box((0.232, 0.016, 0.114)),
        mass=0.45,
        origin=Origin(xyz=(0.0, 0.008, -0.052)),
    )
    model.articulation(
        "cabinet_to_retrieval_flap",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=flap,
        origin=Origin(xyz=(-0.070, FRONT_Y + 0.012, 0.315)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=2.5, lower=0.0, upper=1.20),
    )

    _add_spiral_stage(
        model,
        name="spiral_stage_bottom",
        mount_xyz=(-0.0625, -0.008, 0.640),
        steel=steel,
        tray_gray=tray_gray,
        candy_color=candy_cyan,
    )
    _add_spiral_stage(
        model,
        name="spiral_stage_lower_mid",
        mount_xyz=(-0.0625, -0.008, 0.825),
        steel=steel,
        tray_gray=tray_gray,
        candy_color=candy_magenta,
    )
    _add_spiral_stage(
        model,
        name="spiral_stage_upper_mid",
        mount_xyz=(-0.0625, -0.008, 1.010),
        steel=steel,
        tray_gray=tray_gray,
        candy_color=candy_orange,
    )
    _add_spiral_stage(
        model,
        name="spiral_stage_top",
        mount_xyz=(-0.0625, -0.008, 1.195),
        steel=steel,
        tray_gray=tray_gray,
        candy_color=candy_cyan,
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
