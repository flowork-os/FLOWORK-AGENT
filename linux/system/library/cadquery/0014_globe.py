# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, globe, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: globe

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

def _scale_shape(shape, s):
    """Honor unit_scale (e.g. models authored in mm, exported to meters with
    unit_scale=0.001): uniformly scale the B-rep about the origin."""
    if not s or s == 1.0 or shape is None:
        return shape
    try:
        return shape.transformGeometry(cq.Matrix([[s, 0, 0, 0], [0, s, 0, 0], [0, 0, s, 0]]))
    except Exception:
        return shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_scale_shape(_to_shape(model), kwargs.get("unit_scale", 1.0)),
                   name=name if isinstance(name, str) else None)

def mesh_from_geometry(geometry, name=None, **kwargs):
    return _CQMesh(_scale_shape(_to_shape(geometry), kwargs.get("unit_scale", 1.0)),
                   name=name if isinstance(name, str) else None)

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
        self._raw_verts = [tuple(v) for v in (vertices or [])]
        self._raw_faces = [tuple(f) for f in (faces or [])]
        self._shape = None
        self._tess = None

    # subclasses call this with their cadquery shape
    def _set(self, shape):
        self._shape = _to_shape(shape) if not isinstance(shape, cq.Shape) else shape
        self._tess = None
        return self

    def _tessellate(self):
        """Triangle mesh (vertices, faces) of the B-rep — some model scripts read
        .vertices/.faces to manipulate raw geometry (e.g. axis swaps)."""
        if self._tess is None:
            if self._shape is None:
                self._tess = (list(self._raw_verts), list(self._raw_faces))
            else:
                try:
                    vs, ts = self._shape.tessellate(0.0005)
                    self._tess = ([(v.x, v.y, v.z) for v in vs],
                                  [tuple(int(i) for i in t) for t in ts])
                except Exception:
                    self._tess = (list(self._raw_verts), list(self._raw_faces))
        return self._tess

    @property
    def vertices(self):
        return self._raw_verts if self._raw_verts else self._tessellate()[0]

    @vertices.setter
    def vertices(self, v):
        # capture the B-rep's faces first so a vertices-ONLY reassignment
        # (read mesh -> transform verts -> assign back) doesn't lose the faces
        if self._shape is not None and not self._raw_faces:
            self._raw_faces = list(self._tessellate()[1])
        self._raw_verts = [tuple(x) for x in (v or [])]
        self._shape = None; self._tess = None

    @property
    def faces(self):
        return self._raw_faces if self._raw_faces else self._tessellate()[1]

    @faces.setter
    def faces(self, f):
        if self._shape is not None and not self._raw_verts:
            self._raw_verts = list(self._tessellate()[0])
        self._raw_faces = [tuple(x) for x in (f or [])]
        self._shape = None; self._tess = None

    def _cq(self):
        if self._shape is not None:
            return self._shape
        return _solid_from_triangles(self._raw_verts, self._raw_faces)

    # ---- mesh-style authoring (raw triangle fallback path) ----
    def add_vertex(self, x, y, z):
        self._raw_verts.append((float(x), float(y), float(z)))
        self._shape = None; self._tess = None
        return len(self._raw_verts) - 1

    def add_face(self, a, b, c):
        self._raw_faces.append((int(a), int(b), int(c)))
        self._shape = None; self._tess = None

    def copy(self):
        g = MeshGeometry(self._raw_verts, self._raw_faces)
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
        if self._shape is None and not self._raw_verts:
            self._shape = o          # empty accumulator: adopt other's shape
        else:
            a = self._cq()
            try:
                fused = a.fuse(o)
                if fused is None or fused.wrapped is None or fused.wrapped.IsNull():
                    raise ValueError("null fuse result")
                self._shape = fused
            except Exception:
                # OCC fuse can fail/return null on many thin/degenerate parts
                # (e.g. a balloon whisk's wire loops) — fall back to a non-boolean
                # Compound, which is equivalent for surface sampling / rendering.
                self._shape = cq.Compound.makeCompound([a, o])
        self._tess = None
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

# ===== brackets_hinges_bezels (48 syms) =====
_EPS = 1e-9

def _dot(a, b):
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])

def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def _norm(v):
    return math.sqrt(_dot(v, v))

def _normalize_vec(v, *, name="vector"):
    n = _norm(v)
    if n <= _EPS:
        raise ValidationError(f"{name} must be non-zero")
    return (v[0] / n, v[1] / n, v[2] / n)

def _brackets_hinges_bezels_clamp(value, lo, hi):
    return min(max(float(value), float(lo)), float(hi))

def _identity4():
    return (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )

def _rpy_matrix(roll, pitch, yaw):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp, cp * sr, cp * cr),
    )

def _origin_to_mat4(origin):
    if origin is None:
        return _identity4()
    ox, oy, oz = origin.xyz
    rr, rp, ry = origin.rpy
    r = _rpy_matrix(float(rr), float(rp), float(ry))
    return (
        (r[0][0], r[0][1], r[0][2], float(ox)),
        (r[1][0], r[1][1], r[1][2], float(oy)),
        (r[2][0], r[2][1], r[2][2], float(oz)),
        (0.0, 0.0, 0.0, 1.0),
    )

def _mat4_vec3(mat, vec):
    x, y, z = vec
    return (
        mat[0][0] * x + mat[0][1] * y + mat[0][2] * z + mat[0][3],
        mat[1][0] * x + mat[1][1] * y + mat[1][2] * z + mat[1][3],
        mat[2][0] * x + mat[2][1] * y + mat[2][2] * z + mat[2][3],
    )

def _mat3_from_mat4(mat):
    return (
        (mat[0][0], mat[0][1], mat[0][2]),
        (mat[1][0], mat[1][1], mat[1][2]),
        (mat[2][0], mat[2][1], mat[2][2]),
    )

def _mat3_transpose(mat):
    return (
        (mat[0][0], mat[1][0], mat[2][0]),
        (mat[0][1], mat[1][1], mat[2][1]),
        (mat[0][2], mat[1][2], mat[2][2]),
    )

def _mat3_vec3(mat, vec):
    return (
        mat[0][0] * vec[0] + mat[0][1] * vec[1] + mat[0][2] * vec[2],
        mat[1][0] * vec[0] + mat[1][1] * vec[1] + mat[1][2] * vec[2],
        mat[2][0] * vec[0] + mat[2][1] * vec[1] + mat[2][2] * vec[2],
    )

def _mat3_mul(a, b):
    rows = []
    for i in range(3):
        rows.append(tuple(
            a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j] for j in range(3)
        ))
    return (rows[0], rows[1], rows[2])

def _mat3_from_columns(a, b, c):
    return ((a[0], b[0], c[0]), (a[1], b[1], c[1]), (a[2], b[2], c[2]))

def _mat4_inverse_rigid(tf):
    rot = _mat3_from_mat4(tf)
    rot_t = _mat3_transpose(rot)
    trans = (float(tf[0][3]), float(tf[1][3]), float(tf[2][3]))
    inv_trans = _mat3_vec3(rot_t, (-trans[0], -trans[1], -trans[2]))
    return (
        (rot_t[0][0], rot_t[0][1], rot_t[0][2], inv_trans[0]),
        (rot_t[1][0], rot_t[1][1], rot_t[1][2], inv_trans[1]),
        (rot_t[2][0], rot_t[2][1], rot_t[2][2], inv_trans[2]),
        (0.0, 0.0, 0.0, 1.0),
    )

def _mat4_transform_direction(tf, vec):
    return _mat3_vec3(_mat3_from_mat4(tf), vec)

def _axis_angle_matrix(axis, angle):
    ax = _normalize_vec(axis, name="axis")
    x, y, z = ax
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1.0 - c
    return (
        (t * x * x + c, t * x * y - s * z, t * x * z + s * y),
        (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c),
    )

def _geometry_local_aabb(geometry):
    if isinstance(geometry, Box):
        sx, sy, sz = geometry.size
        return ((-sx / 2.0, -sy / 2.0, -sz / 2.0), (sx / 2.0, sy / 2.0, sz / 2.0))
    if isinstance(geometry, Cylinder):
        r = float(geometry.radius)
        length = float(geometry.length)
        return ((-r, -r, -length / 2.0), (r, r, length / 2.0))
    if isinstance(geometry, Sphere):
        r = float(geometry.radius)
        return ((-r, -r, -r), (r, r, r))
    shape = _to_shape(geometry)
    bb = shape.BoundingBox()
    return ((bb.xmin, bb.ymin, bb.zmin), (bb.xmax, bb.ymax, bb.zmax))

def _iter_subject_items(subject, *, prefer_collisions):
    if isinstance(subject, Part):
        collisions = list(getattr(subject, "collisions", []) or [])
        if prefer_collisions and collisions:
            items = collisions
        elif subject.visuals:
            items = list(subject.visuals)
        else:
            items = collisions
        return [
            (item.geometry, _origin_to_mat4(getattr(item, "origin", None)))
            for item in items
            if getattr(item, "geometry", None) is not None
        ]
    if isinstance(subject, Visual):
        return [(subject.geometry, _origin_to_mat4(subject.origin))]
    return [(subject, _identity4())]

@dataclass(frozen=True)
class _SurfaceHit:
    point: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    distance: float

def _closest_point_on_box(point, size):
    hx, hy, hz = float(size[0]) * 0.5, float(size[1]) * 0.5, float(size[2]) * 0.5
    x, y, z = point
    clamped = (_brackets_hinges_bezels_clamp(x, -hx, hx), _brackets_hinges_bezels_clamp(y, -hy, hy), _brackets_hinges_bezels_clamp(z, -hz, hz))
    inside = abs(x) <= hx and abs(y) <= hy and abs(z) <= hz
    if inside:
        face_dist = (hx - abs(x), hy - abs(y), hz - abs(z))
        axis = min(range(3), key=lambda idx: face_dist[idx])
        sign = 1.0 if point[axis] >= 0.0 else -1.0
        nearest = [x, y, z]
        nearest[axis] = (hx, hy, hz)[axis] * sign
        normal = [0.0, 0.0, 0.0]
        normal[axis] = sign
        return (nearest[0], nearest[1], nearest[2]), (normal[0], normal[1], normal[2])
    dx = x - clamped[0]
    dy = y - clamped[1]
    dz = z - clamped[2]
    axis = max(range(3), key=lambda idx: abs((dx, dy, dz)[idx]))
    delta = (dx, dy, dz)[axis]
    sign = 1.0 if delta >= 0.0 else -1.0
    normal = [0.0, 0.0, 0.0]
    normal[axis] = sign
    return clamped, (normal[0], normal[1], normal[2])

def _closest_point_on_cylinder(point, radius, length):
    x, y, z = point
    half = float(length) * 0.5
    radial = math.hypot(x, y)
    if radial <= _EPS:
        rx, ry = 1.0, 0.0
    else:
        rx, ry = x / radial, y / radial
    side = (rx * radius, ry * radius, _brackets_hinges_bezels_clamp(z, -half, half))
    side_d2 = (x - side[0]) ** 2 + (y - side[1]) ** 2 + (z - side[2]) ** 2

    def cap_candidate(sign):
        cap_z = sign * half
        if radial <= radius:
            cap_xy = (x, y)
        else:
            cap_xy = (rx * radius, ry * radius)
        cap = (cap_xy[0], cap_xy[1], cap_z)
        d2 = (x - cap[0]) ** 2 + (y - cap[1]) ** 2 + (z - cap[2]) ** 2
        return cap, d2

    top, top_d2 = cap_candidate(+1.0)
    bottom, bottom_d2 = cap_candidate(-1.0)
    if side_d2 <= top_d2 and side_d2 <= bottom_d2:
        return side, (rx, ry, 0.0)
    if top_d2 <= bottom_d2:
        return top, (0.0, 0.0, 1.0)
    return bottom, (0.0, 0.0, -1.0)

def _query_surface_on_element(geometry, tf, *, point_hint):
    inv_tf = _mat4_inverse_rigid(tf)
    point_local = _mat4_vec3(inv_tf, point_hint)

    if isinstance(geometry, Sphere):
        radius = float(geometry.radius)
        direction = point_local
        if _norm(direction) <= _EPS:
            direction = (1.0, 0.0, 0.0)
        normal_local = _normalize_vec(direction, name="sphere query direction")
        surface_local = (normal_local[0] * radius, normal_local[1] * radius, normal_local[2] * radius)
    elif isinstance(geometry, Box):
        surface_local, normal_local = _closest_point_on_box(point_local, geometry.size)
    elif isinstance(geometry, Cylinder):
        surface_local, normal_local = _closest_point_on_cylinder(
            point_local, radius=float(geometry.radius), length=float(geometry.length)
        )
    else:
        # generic B-rep: approximate by its local AABB treated as a box
        (mn, mx) = _geometry_local_aabb(geometry)
        ctr = ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5)
        size = (mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
        rel = (point_local[0] - ctr[0], point_local[1] - ctr[1], point_local[2] - ctr[2])
        sp, normal_local = _closest_point_on_box(rel, size)
        surface_local = (sp[0] + ctr[0], sp[1] + ctr[1], sp[2] + ctr[2])

    distance = _norm(
        (point_local[0] - surface_local[0],
         point_local[1] - surface_local[1],
         point_local[2] - surface_local[2])
    )
    point_world = _mat4_vec3(tf, surface_local)
    normal_world = _normalize_vec(_mat4_transform_direction(tf, normal_local), name="surface normal")
    return _SurfaceHit(point=point_world, normal=normal_world, distance=distance)

def _query_subject_surface_at_point(subject, *, point_hint, asset_root=None, prefer_collisions):
    best = None
    for geometry, tf in _iter_subject_items(subject, prefer_collisions=prefer_collisions):
        hit = _query_surface_on_element(geometry, tf, point_hint=point_hint)
        if best is None or hit.distance < best.distance:
            best = hit
    if best is None:
        raise ValidationError("target has no geometry to query")
    return best

def _shim_axis_vector(axis):
    table = {
        "+x": (1.0, 0.0, 0.0), "-x": (-1.0, 0.0, 0.0),
        "+y": (0.0, 1.0, 0.0), "-y": (0.0, -1.0, 0.0),
        "+z": (0.0, 0.0, 1.0), "-z": (0.0, 0.0, -1.0),
    }
    axis_key = axis.strip().lower()
    if axis_key not in table:
        raise ValidationError(f"Invalid axis {axis!r}; expected one of: {', '.join(sorted(table))}")
    return table[axis_key]

def _child_local_basis_for_axis(axis):
    basis = {
        "+z": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "-z": ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
        "+x": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        "-x": ((0.0, 1.0, 0.0), (0.0, 0.0, -1.0), (-1.0, 0.0, 0.0)),
        "+y": ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        "-y": ((0.0, 0.0, -1.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0)),
    }
    axis_key = axis.strip().lower()
    if axis_key not in basis:
        raise ValidationError(f"Invalid axis {axis!r}; expected one of: {', '.join(sorted(basis))}")
    return basis[axis_key]

def _rotation_for_surface_frame(frame, *, child_axis, spin):
    local_basis = _child_local_basis_for_axis(child_axis)
    world_basis = _mat3_from_columns(frame.tangent_u, frame.tangent_v, frame.normal)
    local_basis_mat = _mat3_from_columns(local_basis[0], local_basis[1], local_basis[2])
    base = _mat3_mul(world_basis, _mat3_transpose(local_basis_mat))
    if abs(float(spin)) <= _EPS:
        return base
    spin_world = _axis_angle_matrix(frame.normal, float(spin))
    return _mat3_mul(spin_world, base)

def _cross_z(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def _point_in_triangle(p, a, b, c):
    eps = 1e-9
    c1 = _cross_z(a, b, p)
    c2 = _cross_z(b, c, p)
    c3 = _cross_z(c, a, p)
    return (c1 > eps and c2 > eps and c3 > eps) or (c1 < -eps and c2 < -eps and c3 < -eps)

def _triangulate_polygon(points):
    if len(points) < 3:
        return []
    indices = list(range(len(points)))
    triangles = []
    guard = 0
    max_guard = len(points) * len(points)
    while len(indices) > 3:
        ear_found = False
        for i in range(len(indices)):
            i_prev = indices[i - 1]
            i_curr = indices[i]
            i_next = indices[(i + 1) % len(indices)]
            if _cross_z(points[i_prev], points[i_curr], points[i_next]) <= 0:
                continue
            ear = True
            for j in indices:
                if j in (i_prev, i_curr, i_next):
                    continue
                if _point_in_triangle(points[j], points[i_prev], points[i_curr], points[i_next]):
                    ear = False
                    break
            if ear:
                triangles.append((i_prev, i_curr, i_next))
                del indices[i]
                ear_found = True
                break
        guard += 1
        if not ear_found or guard > max_guard:
            raise ValidationError("Failed to triangulate profile; ensure it is simple")
    triangles.append((indices[0], indices[1], indices[2]))
    return triangles

def _geom_vertices_faces(geom):
    """Return (vertices, faces) for a shim geometry, tessellating a B-rep if needed."""
    if getattr(geom, "vertices", None) and getattr(geom, "faces", None):
        return list(geom.vertices), list(geom.faces)
    shape = _to_shape(geom)
    try:
        verts, tris = shape.tessellate(0.001, 0.1)
    except TypeError:
        verts, tris = shape.tessellate(0.001)
    vertices = [(float(v.x), float(v.y), float(v.z)) for v in verts]
    faces = [(int(t[0]), int(t[1]), int(t[2])) for t in tris]
    return vertices, faces

def _subdivide_mesh_geometry_to_size(geometry, *, max_edge):
    if max_edge is None:
        return geometry
    max_edge_value = float(max_edge)
    if max_edge_value <= 0.0:
        raise ValidationError("max_edge must be positive")
    if not geometry.vertices or not geometry.faces:
        return geometry
    import trimesh
    vertices, faces = trimesh.remesh.subdivide_to_size(
        geometry.vertices, geometry.faces, max_edge=max_edge_value
    )
    return MeshGeometry(
        vertices=[(float(v[0]), float(v[1]), float(v[2])) for v in vertices],
        faces=[(int(f[0]), int(f[1]), int(f[2])) for f in faces],
    )

def _normalize_profile_points(profile):
    return _ensure_ccw(_profile_points_2d(profile))

def _planar_profile_cap(profile, *, max_edge):
    points = _normalize_profile_points(profile)
    faces = _triangulate_polygon(points)
    cap = MeshGeometry(
        vertices=[(float(x), float(y), 0.0) for x, y in points],
        faces=[(int(a), int(b), int(c)) for a, b, c in faces],
    )
    if not cap.faces:
        raise ValidationError("profile triangulation produced no faces")
    return _subdivide_mesh_geometry_to_size(cap, max_edge=max_edge)

def _boundary_loop_for_planar_mesh(geometry, *, boundary_profile):
    edge_counts = {}
    for a, b, c in geometry.faces:
        for u, v in ((a, b), (b, c), (c, a)):
            key = (u, v) if u < v else (v, u)
            edge_counts[key] = edge_counts.get(key, 0) + 1
    boundary_vertices = sorted(
        {index for edge, count in edge_counts.items() if count == 1 for index in edge}
    )
    if not boundary_vertices:
        raise ValidationError("profile mesh has no boundary loop")

    cumulative = [0.0]
    for i, a in enumerate(boundary_profile):
        b = boundary_profile[(i + 1) % len(boundary_profile)]
        cumulative.append(
            cumulative[-1] + math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))
        )
    perimeter = cumulative[-1]
    if perimeter <= _EPS:
        raise ValidationError("profile perimeter must be non-zero")

    def _dist_to_seg(point, a, b):
        seg_x = float(b[0]) - float(a[0])
        seg_y = float(b[1]) - float(a[1])
        seg_len2 = seg_x * seg_x + seg_y * seg_y
        if seg_len2 <= _EPS:
            return math.hypot(point[0] - a[0], point[1] - a[1]), 0.0
        rel_x = float(point[0]) - float(a[0])
        rel_y = float(point[1]) - float(a[1])
        t = _brackets_hinges_bezels_clamp((rel_x * seg_x + rel_y * seg_y) / seg_len2, 0.0, 1.0)
        cx = float(a[0]) + seg_x * t
        cy = float(a[1]) + seg_y * t
        return math.hypot(float(point[0]) - cx, float(point[1]) - cy), t

    ordered = []
    for index in boundary_vertices:
        point = (float(geometry.vertices[index][0]), float(geometry.vertices[index][1]))
        best_distance = float("inf")
        best_arclength = 0.0
        for segment_index, a in enumerate(boundary_profile):
            b = boundary_profile[(segment_index + 1) % len(boundary_profile)]
            distance, t = _dist_to_seg(point, a, b)
            if distance + 1e-9 < best_distance:
                best_distance = distance
                best_arclength = (
                    cumulative[segment_index]
                    + (cumulative[segment_index + 1] - cumulative[segment_index]) * t
                )
        if best_distance > 1e-5:
            raise ValidationError("profile mesh boundary deviated from source profile")
        if best_arclength >= perimeter - 1e-8:
            best_arclength = 0.0
        ordered.append((best_arclength, index))

    ordered.sort(key=lambda item: item[0])
    loop = [index for _, index in ordered]
    area = 0.0
    for i, index in enumerate(loop):
        x1, y1, _ = geometry.vertices[index]
        x2, y2, _ = geometry.vertices[loop[(i + 1) % len(loop)]]
        area += x1 * y2 - x2 * y1
    if area < 0.0:
        loop.reverse()
    return loop

def _solid_from_planar_profile_cap(cap, *, boundary_profile, thickness):
    thickness_value = float(thickness)
    if thickness_value <= 0.0:
        raise ValidationError("thickness must be positive")
    loop = _boundary_loop_for_planar_mesh(cap, boundary_profile=boundary_profile)
    vertex_count = len(cap.vertices)
    solid = MeshGeometry(
        vertices=[
            *[(float(x), float(y), 0.0) for x, y, _ in cap.vertices],
            *[(float(x), float(y), -thickness_value) for x, y, _ in cap.vertices],
        ],
        faces=[],
    )
    for a, b, c in cap.faces:
        solid.add_face(a, b, c)
    offset = vertex_count
    for a, b, c in cap.faces:
        solid.add_face(offset + c, offset + b, offset + a)
    for i, a in enumerate(loop):
        b = loop[(i + 1) % len(loop)]
        solid.add_face(a, b, offset + b)
        solid.add_face(a, offset + b, offset + a)
    return solid

def _fallback_profile_solid(profile, *, hole_profiles, thickness):
    """Direct prism builder (visible cap on z=0, thickness toward -z).

    Holes are not supported in this fallback path; they are ignored.
    """
    points = _normalize_profile_points(profile)
    faces = _triangulate_polygon(points)
    cap = MeshGeometry(vertices=[(float(x), float(y), 0.0) for x, y in points],
                       faces=[(int(a), int(b), int(c)) for a, b, c in faces])
    return _solid_from_planar_profile_cap(cap, boundary_profile=points, thickness=thickness)

def _mesh_geometry_from_subject(mesh):
    if isinstance(mesh, MeshGeometry):
        if getattr(mesh, "vertices", None) and getattr(mesh, "faces", None):
            return mesh.copy()
        v, f = _geom_vertices_faces(mesh)
        return MeshGeometry(vertices=v, faces=f)
    if isinstance(mesh, _CQMesh):
        v, f = _geom_vertices_faces(mesh)
        return MeshGeometry(vertices=v, faces=f)
    raise ValidationError(f"mesh must be a MeshGeometry, got {type(mesh).__name__}")

def _subject_single_world_sphere(subject, *, prefer_collisions):
    items = _iter_subject_items(subject, prefer_collisions=prefer_collisions)
    if len(items) != 1:
        return None
    geometry, tf = items[0]
    if not isinstance(geometry, Sphere):
        return None
    return _mat4_vec3(tf, (0.0, 0.0, 0.0)), float(geometry.radius)

def _subject_single_world_cylinder(subject, *, prefer_collisions):
    items = _iter_subject_items(subject, prefer_collisions=prefer_collisions)
    if len(items) != 1:
        return None
    geometry, tf = items[0]
    if not isinstance(geometry, Cylinder):
        return None
    center = _mat4_vec3(tf, (0.0, 0.0, 0.0))
    axis_world = _normalize_vec(_mat4_transform_direction(tf, (0.0, 0.0, 1.0)), name="cylinder axis")
    return center, axis_world, float(geometry.radius), float(geometry.length)

def _wrap_mesh_onto_sphere(geometry, *, frame, sphere_center, sphere_radius, child_axis,
                           visible_relief, spin):
    rot = _rotation_for_surface_frame(frame, child_axis=child_axis, spin=float(spin))
    axis_local = _shim_axis_vector(child_axis)
    outer_support = max(_dot(vertex, axis_local) for vertex in geometry.vertices)
    wrapped = []
    for vertex in geometry.vertices:
        local_proj = _dot(vertex, axis_local)
        depth_behind = outer_support - local_proj
        in_plane_local = (
            float(vertex[0]) - axis_local[0] * local_proj,
            float(vertex[1]) - axis_local[1] * local_proj,
            float(vertex[2]) - axis_local[2] * local_proj,
        )
        tangent_offset = _mat3_vec3(rot, in_plane_local)
        tangent_distance = _norm(tangent_offset)
        if tangent_distance <= _EPS:
            surface_normal = frame.normal
        else:
            tangent_dir = (tangent_offset[0] / tangent_distance,
                           tangent_offset[1] / tangent_distance,
                           tangent_offset[2] / tangent_distance)
            angle = tangent_distance / float(sphere_radius)
            surface_normal = _normalize_vec(
                (math.cos(angle) * frame.normal[0] + math.sin(angle) * tangent_dir[0],
                 math.cos(angle) * frame.normal[1] + math.sin(angle) * tangent_dir[1],
                 math.cos(angle) * frame.normal[2] + math.sin(angle) * tangent_dir[2]),
                name="sphere wrap normal",
            )
        surface_point = (
            sphere_center[0] + surface_normal[0] * float(sphere_radius),
            sphere_center[1] + surface_normal[1] * float(sphere_radius),
            sphere_center[2] + surface_normal[2] * float(sphere_radius),
        )
        wrapped.append((
            surface_point[0] + surface_normal[0] * (float(visible_relief) - depth_behind),
            surface_point[1] + surface_normal[1] * (float(visible_relief) - depth_behind),
            surface_point[2] + surface_normal[2] * (float(visible_relief) - depth_behind),
        ))
    return MeshGeometry(vertices=wrapped, faces=list(geometry.faces))

def _wrap_mesh_onto_cylinder(geometry, *, frame, cylinder_center, cylinder_axis, cylinder_radius,
                             cylinder_length, child_axis, visible_relief, spin):
    if abs(_dot(frame.normal, cylinder_axis)) >= 0.2:
        return None
    rel_anchor = (frame.point[0] - cylinder_center[0],
                  frame.point[1] - cylinder_center[1],
                  frame.point[2] - cylinder_center[2])
    anchor_axial = _dot(rel_anchor, cylinder_axis)
    anchor_radial = (rel_anchor[0] - cylinder_axis[0] * anchor_axial,
                     rel_anchor[1] - cylinder_axis[1] * anchor_axial,
                     rel_anchor[2] - cylinder_axis[2] * anchor_axial)
    if _norm(anchor_radial) <= _EPS:
        return None
    anchor_normal = _normalize_vec(anchor_radial, name="cylinder wrap normal")
    circum_axis = _normalize_vec(_cross(cylinder_axis, anchor_normal),
                                 name="cylinder circumferential tangent")
    half_length = float(cylinder_length) * 0.5
    rot = _rotation_for_surface_frame(frame, child_axis=child_axis, spin=float(spin))
    axis_local = _shim_axis_vector(child_axis)
    outer_support = max(_dot(vertex, axis_local) for vertex in geometry.vertices)
    wrapped = []
    for vertex in geometry.vertices:
        local_proj = _dot(vertex, axis_local)
        depth_behind = outer_support - local_proj
        in_plane_local = (
            float(vertex[0]) - axis_local[0] * local_proj,
            float(vertex[1]) - axis_local[1] * local_proj,
            float(vertex[2]) - axis_local[2] * local_proj,
        )
        tangent_offset = _mat3_vec3(rot, in_plane_local)
        circum_distance = _dot(tangent_offset, circum_axis)
        axial_distance = _dot(tangent_offset, cylinder_axis)
        axial = anchor_axial + axial_distance
        if abs(axial) > half_length + 1e-9:
            return None
        angle = circum_distance / float(cylinder_radius)
        turn = _axis_angle_matrix(cylinder_axis, angle)
        surface_normal = _normalize_vec(_mat3_vec3(turn, anchor_normal),
                                        name="cylinder wrap rotated normal")
        surface_point = (
            cylinder_center[0] + cylinder_axis[0] * axial + surface_normal[0] * float(cylinder_radius),
            cylinder_center[1] + cylinder_axis[1] * axial + surface_normal[1] * float(cylinder_radius),
            cylinder_center[2] + cylinder_axis[2] * axial + surface_normal[2] * float(cylinder_radius),
        )
        wrapped.append((
            surface_point[0] + surface_normal[0] * (float(visible_relief) - depth_behind),
            surface_point[1] + surface_normal[1] * (float(visible_relief) - depth_behind),
            surface_point[2] + surface_normal[2] * (float(visible_relief) - depth_behind),
        ))
    return MeshGeometry(vertices=wrapped, faces=list(geometry.faces))

def _wrap_mesh_onto_surface_nearest(geometry, *, frame, target, child_axis, visible_relief, spin,
                                    prefer_collisions):
    rot = _rotation_for_surface_frame(frame, child_axis=child_axis, spin=float(spin))
    axis_local = _shim_axis_vector(child_axis)
    outer_support = max(_dot(vertex, axis_local) for vertex in geometry.vertices)
    wrapped = []
    for vertex in geometry.vertices:
        local_proj = _dot(vertex, axis_local)
        depth_behind = outer_support - local_proj
        in_plane_local = (
            float(vertex[0]) - axis_local[0] * local_proj,
            float(vertex[1]) - axis_local[1] * local_proj,
            float(vertex[2]) - axis_local[2] * local_proj,
        )
        plane_offset = _mat3_vec3(rot, in_plane_local)
        query_point = (frame.point[0] + plane_offset[0],
                       frame.point[1] + plane_offset[1],
                       frame.point[2] + plane_offset[2])
        hit = _query_subject_surface_at_point(target, point_hint=query_point,
                                              prefer_collisions=prefer_collisions)
        wrapped.append((
            hit.point[0] + hit.normal[0] * (float(visible_relief) - depth_behind),
            hit.point[1] + hit.normal[1] * (float(visible_relief) - depth_behind),
            hit.point[2] + hit.normal[2] * (float(visible_relief) - depth_behind),
        ))
    return MeshGeometry(vertices=wrapped, faces=list(geometry.faces))

def _normalize_surface_wrap_mapping(mapping):
    mapping_key = str(mapping).strip().lower()
    if mapping_key not in {"auto", "intrinsic", "nearest"}:
        raise ValidationError("mapping must be one of: 'auto', 'intrinsic', 'nearest'")
    return mapping_key

def _resolve_surface_max_edge(*, surface_max_edge, max_edge):
    if surface_max_edge is None:
        return max_edge
    if max_edge is None:
        return surface_max_edge
    if abs(float(surface_max_edge) - float(max_edge)) > 1e-12:
        raise ValidationError("Provide only one of surface_max_edge or max_edge")
    return surface_max_edge

def wrap_mesh_onto_surface(
    mesh,
    target,
    *,
    point_hint=None,
    direction=None,
    child_axis="+z",
    visible_relief=0.0,
    mapping="auto",
    surface_max_edge=None,
    max_edge=None,
    spin=0.0,
    asset_root=None,
    prefer_collisions=False,
    up_hint=(0.0, 0.0, 1.0),
):
    """Conform a mesh onto a target surface and return a baked MeshGeometry."""
    mapping_mode = _normalize_surface_wrap_mapping(mapping)
    frame = surface_frame(target, point_hint=point_hint, direction=direction,
                          prefer_collisions=prefer_collisions, up_hint=up_hint)
    resolved_max_edge = _resolve_surface_max_edge(surface_max_edge=surface_max_edge,
                                                  max_edge=max_edge)
    geometry = _mesh_geometry_from_subject(mesh)
    geometry = _subdivide_mesh_geometry_to_size(geometry, max_edge=resolved_max_edge)
    if not geometry.vertices:
        raise ValidationError("mesh has no vertices")

    if mapping_mode != "nearest":
        sphere_info = _subject_single_world_sphere(target, prefer_collisions=prefer_collisions)
        if sphere_info is not None:
            sphere_center, sphere_radius = sphere_info
            return _wrap_mesh_onto_sphere(geometry, frame=frame, sphere_center=sphere_center,
                                          sphere_radius=sphere_radius, child_axis=child_axis,
                                          visible_relief=float(visible_relief), spin=float(spin))
        cylinder_info = _subject_single_world_cylinder(target, prefer_collisions=prefer_collisions)
        if cylinder_info is not None:
            cc, ca, cr, cl = cylinder_info
            intrinsic = _wrap_mesh_onto_cylinder(geometry, frame=frame, cylinder_center=cc,
                                                 cylinder_axis=ca, cylinder_radius=cr,
                                                 cylinder_length=cl, child_axis=child_axis,
                                                 visible_relief=float(visible_relief),
                                                 spin=float(spin))
            if intrinsic is not None:
                return intrinsic
        if mapping_mode == "intrinsic":
            raise ValidationError(
                "Intrinsic surface wrapping is only supported for spheres and cylinder sidewalls"
            )

    return _wrap_mesh_onto_surface_nearest(geometry, frame=frame, target=target,
                                           child_axis=child_axis,
                                           visible_relief=float(visible_relief), spin=float(spin),
                                           prefer_collisions=prefer_collisions)

def wrap_profile_onto_surface(
    profile,
    target,
    *,
    thickness,
    hole_profiles=(),
    point_hint=None,
    direction=None,
    visible_relief=0.0,
    mapping="auto",
    surface_max_edge=None,
    max_edge=None,
    spin=0.0,
    asset_root=None,
    prefer_collisions=False,
    up_hint=(0.0, 0.0, 1.0),
):
    """Wrap a 2D profile with thickness directly onto a target surface."""
    thickness_value = float(thickness)
    if thickness_value <= 0.0:
        raise ValidationError("thickness must be positive")
    resolved_max_edge = _resolve_surface_max_edge(surface_max_edge=surface_max_edge,
                                                  max_edge=max_edge)
    points = _normalize_profile_points(profile)
    holes = [_normalize_profile_points(h) for h in hole_profiles]

    if holes:
        fallback = _fallback_profile_solid(points, hole_profiles=holes, thickness=thickness_value)
        return wrap_mesh_onto_surface(fallback, target, point_hint=point_hint, direction=direction,
                                      child_axis="+z", visible_relief=visible_relief, mapping=mapping,
                                      surface_max_edge=resolved_max_edge, spin=spin,
                                      prefer_collisions=prefer_collisions, up_hint=up_hint)

    cap = _planar_profile_cap(points, max_edge=resolved_max_edge)
    try:
        solid = _solid_from_planar_profile_cap(cap, boundary_profile=points,
                                               thickness=thickness_value)
        return wrap_mesh_onto_surface(solid, target, point_hint=point_hint, direction=direction,
                                      child_axis="+z", visible_relief=visible_relief, mapping=mapping,
                                      spin=spin, prefer_collisions=prefer_collisions, up_hint=up_hint)
    except ValidationError as exc:
        if "profile mesh boundary" not in str(exc):
            raise

    fallback = _fallback_profile_solid(points, hole_profiles=[], thickness=thickness_value)
    return wrap_mesh_onto_surface(fallback, target, point_hint=point_hint, direction=direction,
                                  child_axis="+z", visible_relief=visible_relief, mapping=mapping,
                                  surface_max_edge=resolved_max_edge, spin=spin,
                                  prefer_collisions=prefer_collisions, up_hint=up_hint)

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

# ===== sweeps (41 syms) =====
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

def sample_catmull_rom_spline_2d(points, *, samples_per_segment: int = 12,
                                 closed: bool = False, alpha: float = 0.5):
    """Sample a centripetal Catmull-Rom spline through the input 2D points."""
    sampled = _sample_catmull_rom_spline(
        points, samples_per_segment=samples_per_segment, closed=bool(closed), alpha=float(alpha),
    )
    return [(float(x), float(y)) for (x, y) in sampled]

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

class SurfaceFrame:
    """Result of a surface query: a point on the surface, the outward unit
    normal there, and two orthonormal surface tangents."""
    __slots__ = ("point", "normal", "tangent_u", "tangent_v")

    def __init__(self, point, normal, tangent_u, tangent_v):
        self.point = tuple(float(c) for c in point)
        self.normal = tuple(float(c) for c in normal)
        self.tangent_u = tuple(float(c) for c in tangent_u)
        self.tangent_v = tuple(float(c) for c in tangent_v)

    def __repr__(self):
        return "SurfaceFrame(point=%r, normal=%r)" % (self.point, self.normal)

def _sweeps_build_surface_tangents(normal, up_hint):
    """Verbatim from sdk placement._sweeps_build_surface_tangents."""
    up = _v_normalize(up_hint)
    projected = (
        up[0] - normal[0] * _v_dot(up, normal),
        up[1] - normal[1] * _v_dot(up, normal),
        up[2] - normal[2] * _v_dot(up, normal),
    )
    if _v_norm(projected) <= _EPS:
        fallback = (1.0, 0.0, 0.0)
        if abs(_v_dot(fallback, normal)) >= 0.95:
            fallback = (0.0, 1.0, 0.0)
        projected = _v_cross(fallback, normal)
    tangent_u = _v_normalize(projected)
    tangent_v = _v_normalize(_v_cross(normal, tangent_u))
    return tangent_u, tangent_v

def _origin_shape(shape, origin):
    """Apply a shim Origin (xyz + rpy radians, URDF Rz@Ry@Rx) to a cq shape."""
    if origin is None:
        return shape
    xyz = tuple(float(v) for v in getattr(origin, "xyz", (0.0, 0.0, 0.0)))
    rpy = tuple(float(v) for v in getattr(origin, "rpy", (0.0, 0.0, 0.0)))
    s = shape
    if any(abs(a) > 0.0 for a in rpy):
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), math.degrees(rpy[0]))
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), math.degrees(rpy[1]))
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), math.degrees(rpy[2]))
    if any(abs(a) > 0.0 for a in xyz):
        s = s.translate(cq.Vector(*xyz))
    return s

def _subject_shape(target, *, prefer_collisions=False):
    """Resolve a Part / Visual / Geometry subject into a single cq.Shape."""
    visuals = getattr(target, "visuals", None)
    collisions = getattr(target, "collisions", None)
    if visuals is not None or collisions is not None:
        items = list(collisions) if (prefer_collisions and collisions) else list(visuals or [])
        if not items:
            items = list(collisions or [])
        shapes = []
        for item in items:
            geom = getattr(item, "geometry", None)
            if geom is None:
                continue
            shapes.append(_origin_shape(_to_shape(geom), getattr(item, "origin", None)))
        if not shapes:
            raise ValidationError("subject has no geometry to query")
        out = shapes[0]
        for s in shapes[1:]:
            out = out.fuse(s)
        return out
    if hasattr(target, "geometry") and hasattr(target, "origin"):
        return _origin_shape(_to_shape(target.geometry), target.origin)
    return _to_shape(target)

def _surface_closest_point_normal(shape, query):
    """Closest point on a cq shape's surface to ``query`` plus the outward
    unit normal there (via OCC BRepExtrema + face geometry)."""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape, BRepExtrema_SupportType
    from OCP.BRepGProp import BRepGProp_Face
    from OCP.TopoDS import TopoDS
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.gp import gp_Pnt, gp_Vec

    vtx = cq.Vertex.makeVertex(float(query[0]), float(query[1]), float(query[2]))
    dss = BRepExtrema_DistShapeShape(shape.wrapped, vtx.wrapped)
    dss.Perform()
    if not dss.IsDone() or dss.NbSolution() < 1:
        raise ValidationError("surface_frame: distance query failed")

    p = dss.PointOnShape1(1)
    point = (p.X(), p.Y(), p.Z())

    normal = None
    if dss.SupportTypeShape1(1) == BRepExtrema_SupportType.BRepExtrema_IsInFace:
        face = TopoDS.Face_s(dss.SupportOnShape1(1))
        u, v = dss.ParOnFaceS1(1)
        bgf = BRepGProp_Face(face)
        pnt = gp_Pnt()
        nrm = gp_Vec()
        bgf.Normal(u, v, pnt, nrm)
        nl = sqrt(nrm.X() ** 2 + nrm.Y() ** 2 + nrm.Z() ** 2)
        if nl > _EPS:
            normal = (nrm.X() / nl, nrm.Y() / nl, nrm.Z() / nl)
            if face.Orientation() == TopAbs_REVERSED:
                normal = (-normal[0], -normal[1], -normal[2])

    if normal is None:
        d = _v_sub((float(query[0]), float(query[1]), float(query[2])), point)
        normal = _v_normalize(d) if _v_norm(d) > _EPS else (0.0, 0.0, 1.0)
    return point, normal

def surface_frame(target, *, point_hint=None, direction=None, asset_root=None,
                  prefer_collisions: bool = False, up_hint=(0.0, 0.0, 1.0)):
    """Query a point + tangent frame on the surface of ``target`` (a Part,
    Visual, or geometry). Provide exactly one of ``point_hint`` (nearest
    surface point) or ``direction`` (surface point along that direction)."""
    if (point_hint is None) == (direction is None):
        raise ValidationError("Exactly one of point_hint or direction must be provided")

    shape = _subject_shape(target, prefer_collisions=prefer_collisions)

    query = point_hint
    if direction is not None:
        d = _v_normalize((float(direction[0]), float(direction[1]), float(direction[2])))
        bb = shape.BoundingBox()
        center = ((bb.xmin + bb.xmax) * 0.5, (bb.ymin + bb.ymax) * 0.5, (bb.zmin + bb.zmax) * 0.5)
        size = (bb.xmax - bb.xmin, bb.ymax - bb.ymin, bb.zmax - bb.zmin)
        radius = max(_v_norm(size), 1e-3)
        query = (center[0] + d[0] * radius * 4.0,
                 center[1] + d[1] * radius * 4.0,
                 center[2] + d[2] * radius * 4.0)

    point, normal = _surface_closest_point_normal(shape, query)
    tangent_u, tangent_v = _sweeps_build_surface_tangents(
        normal, (float(up_hint[0]), float(up_hint[1]), float(up_hint[2]))
    )
    return SurfaceFrame(point=point, normal=normal, tangent_u=tangent_u, tangent_v=tangent_v)

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
ASSETS = AssetContext.from_script(__file__)
GLOBE_RADIUS = 0.09
EARTH_TILT = math.radians(23.5)
MERIDIAN_RADIUS = 0.106
MERIDIAN_TUBE_RADIUS = 0.005
MERIDIAN_COLLAR_HEIGHT = 0.012
MERIDIAN_CENTER_Z = MERIDIAN_COLLAR_HEIGHT + MERIDIAN_RADIUS
def _axis_vector() -> tuple[float, float, float]:
    return (math.sin(EARTH_TILT), 0.0, math.cos(EARTH_TILT))
def _lat_lon_direction(lat_deg: float, lon_deg: float) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    )
def _mesh_name(name: str) -> str:
    return str(ASSETS.mesh_path(name))
def _build_meridian_segment(start_deg: float, end_deg: float, name: str):
    arc_points = []
    for step in range(7):
        t = start_deg + (end_deg - start_deg) * step / 6.0
        angle = math.radians(t)
        arc_points.append(
            (
                MERIDIAN_RADIUS * math.cos(angle),
                0.0,
                MERIDIAN_CENTER_Z + MERIDIAN_RADIUS * math.sin(angle),
            )
        )
    geom = tube_from_spline_points(
        arc_points,
        radius=MERIDIAN_TUBE_RADIUS,
        samples_per_segment=8,
        radial_segments=18,
        cap_ends=True,
        up_hint=(0.0, 1.0, 0.0),
    )
    return mesh_from_geometry(geom, _mesh_name(name))
def _build_continent_mesh(
    name: str,
    points: list[tuple[float, float]],
    lat_deg: float,
    lon_deg: float,
):
    outline = sample_catmull_rom_spline_2d(
        points,
        samples_per_segment=12,
        closed=True,
    )
    wrapped = wrap_profile_onto_surface(
        outline,
        Sphere(radius=GLOBE_RADIUS),
        thickness=0.0012,
        direction=_lat_lon_direction(lat_deg, lon_deg),
        mapping="intrinsic",
        visible_relief=0.0005,
        surface_max_edge=0.005,
    )
    return mesh_from_geometry(wrapped, _mesh_name(name))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="articulated_globe", assets=ASSETS)

    wood = model.material("wood", rgba=(0.38, 0.24, 0.14, 1.0))
    dark_wood = model.material("dark_wood", rgba=(0.24, 0.15, 0.09, 1.0))
    brass = model.material("brass", rgba=(0.78, 0.66, 0.34, 1.0))
    aged_brass = model.material("aged_brass", rgba=(0.63, 0.53, 0.28, 1.0))
    ocean = model.material("ocean", rgba=(0.16, 0.38, 0.62, 1.0))
    land = model.material("land", rgba=(0.70, 0.73, 0.55, 1.0))
    paper = model.material("paper", rgba=(0.91, 0.88, 0.77, 1.0))

    axis = _axis_vector()

    base = model.part("base")
    base_profile = [
        (0.0, 0.0),
        (0.048, 0.0),
        (0.092, 0.006),
        (0.108, 0.016),
        (0.104, 0.026),
        (0.086, 0.039),
        (0.061, 0.049),
        (0.036, 0.054),
        (0.0, 0.054),
    ]
    base_mesh = mesh_from_geometry(LatheGeometry(base_profile, segments=56), _mesh_name("globe_base.obj"))
    base.visual(base_mesh, material=wood)
    base.visual(
        Cylinder(radius=0.028, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.060)),
        material=aged_brass,
        name="collar",
    )
    base.visual(
        Cylinder(radius=0.009, length=0.062),
        origin=Origin(xyz=(0.0, 0.0, 0.097)),
        material=brass,
        name="stem",
    )
    base.visual(
        Cylinder(radius=0.012, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.121)),
        material=aged_brass,
        name="socket",
    )
    base.visual(
        Box((0.050, 0.003, 0.018)),
        origin=Origin(xyz=(0.0, 0.084, 0.030), rpy=(0.0, 0.0, 0.0)),
        material=brass,
        name="nameplate",
    )
    base.visual(
        Box((0.056, 0.002, 0.024)),
        origin=Origin(xyz=(0.0, 0.083, 0.030)),
        material=paper,
        name="nameplate_inlay",
    )
    base.inertial = Inertial.from_geometry(
        Cylinder(radius=0.11, length=0.054),
        mass=1.8,
        origin=Origin(xyz=(0.0, 0.0, 0.027)),
    )

    meridian = model.part("meridian")
    meridian.visual(
        Cylinder(radius=0.013, length=MERIDIAN_COLLAR_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, MERIDIAN_COLLAR_HEIGHT * 0.5)),
        material=aged_brass,
        name="meridian_collar",
    )
    for idx, (start, end) in enumerate(
        [
            (-90.0, -30.0),
            (-30.0, 30.0),
            (30.0, 90.0),
            (90.0, 150.0),
            (150.0, 210.0),
            (210.0, 270.0),
        ],
        start=1,
    ):
        meridian.visual(
            _build_meridian_segment(start, end, f"meridian_segment_{idx}.obj"),
            material=brass,
            name=f"meridian_segment_{idx}",
        )
    meridian.visual(
        Box((0.028, 0.004, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, MERIDIAN_COLLAR_HEIGHT + 0.004)),
        material=aged_brass,
        name="saddle",
    )
    for idx, sign in enumerate((1.0, -1.0), start=1):
        meridian.visual(
            Cylinder(radius=0.0065, length=0.016),
            origin=Origin(
                xyz=(
                    sign * axis[0] * 0.099,
                    0.0,
                    MERIDIAN_CENTER_Z + sign * axis[2] * 0.099,
                ),
                rpy=(0.0, EARTH_TILT, 0.0),
            ),
            material=aged_brass,
            name=f"bearing_cup_{idx}",
        )
    meridian.inertial = Inertial.from_geometry(
        Cylinder(radius=0.11, length=0.015),
        mass=0.45,
        origin=Origin(xyz=(0.0, 0.0, MERIDIAN_CENTER_Z)),
    )

    globe = model.part("globe")
    globe.visual(Sphere(radius=GLOBE_RADIUS), material=ocean, name="ocean_shell")

    north_america = _build_continent_mesh(
        "north_america.obj",
        [
            (-0.021, -0.014),
            (-0.018, 0.002),
            (-0.010, 0.014),
            (0.002, 0.018),
            (0.016, 0.012),
            (0.021, 0.002),
            (0.017, -0.010),
            (0.006, -0.020),
            (-0.008, -0.022),
            (-0.018, -0.018),
        ],
        lat_deg=42.0,
        lon_deg=-102.0,
    )
    south_america = _build_continent_mesh(
        "south_america.obj",
        [
            (-0.009, 0.018),
            (0.002, 0.014),
            (0.010, 0.006),
            (0.010, -0.004),
            (0.005, -0.016),
            (-0.001, -0.028),
            (-0.007, -0.034),
            (-0.013, -0.022),
            (-0.014, -0.008),
            (-0.012, 0.006),
        ],
        lat_deg=-17.0,
        lon_deg=-60.0,
    )
    eurasia = _build_continent_mesh(
        "eurasia.obj",
        [
            (-0.034, -0.014),
            (-0.028, 0.000),
            (-0.020, 0.012),
            (-0.008, 0.020),
            (0.008, 0.022),
            (0.024, 0.014),
            (0.036, 0.010),
            (0.042, -0.002),
            (0.032, -0.012),
            (0.014, -0.016),
            (0.002, -0.012),
            (-0.012, -0.020),
            (-0.026, -0.020),
        ],
        lat_deg=48.0,
        lon_deg=58.0,
    )
    africa = _build_continent_mesh(
        "africa.obj",
        [
            (-0.012, 0.018),
            (0.000, 0.024),
            (0.012, 0.016),
            (0.014, 0.002),
            (0.008, -0.016),
            (0.000, -0.028),
            (-0.008, -0.032),
            (-0.016, -0.014),
            (-0.016, 0.004),
        ],
        lat_deg=5.0,
        lon_deg=20.0,
    )
    australia = _build_continent_mesh(
        "australia.obj",
        [
            (-0.014, 0.008),
            (-0.004, 0.014),
            (0.010, 0.012),
            (0.016, 0.004),
            (0.014, -0.006),
            (0.004, -0.012),
            (-0.008, -0.012),
            (-0.016, -0.002),
        ],
        lat_deg=-25.0,
        lon_deg=135.0,
    )
    greenland = _build_continent_mesh(
        "greenland.obj",
        [
            (-0.008, 0.010),
            (-0.002, 0.016),
            (0.006, 0.012),
            (0.008, 0.002),
            (0.004, -0.008),
            (-0.004, -0.010),
            (-0.010, 0.000),
        ],
        lat_deg=73.0,
        lon_deg=-42.0,
    )

    for name, mesh in [
        ("north_america", north_america),
        ("south_america", south_america),
        ("eurasia", eurasia),
        ("africa", africa),
        ("australia", australia),
        ("greenland", greenland),
    ]:
        globe.visual(mesh, material=land, name=name)

    for idx, sign in enumerate((1.0, -1.0), start=1):
        globe.visual(
            Cylinder(radius=0.0048, length=0.010),
            origin=Origin(
                xyz=(
                    sign * axis[0] * 0.094,
                    0.0,
                    sign * axis[2] * 0.094,
                ),
                rpy=(0.0, EARTH_TILT, 0.0),
            ),
            material=aged_brass,
            name=f"polar_pin_{idx}",
        )

    globe.inertial = Inertial.from_geometry(
        Sphere(radius=GLOBE_RADIUS),
        mass=0.95,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
    )

    model.articulation(
        "base_to_meridian",
        ArticulationType.FIXED,
        parent="base",
        child="meridian",
        origin=Origin(xyz=(0.0, 0.0, 0.1265)),
    )
    model.articulation(
        "globe_spin",
        ArticulationType.CONTINUOUS,
        parent="meridian",
        child="globe",
        origin=Origin(xyz=(0.0, 0.0, MERIDIAN_CENTER_Z)),
        axis=axis,
        motion_limits=MotionLimits(effort=2.5, velocity=3.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
