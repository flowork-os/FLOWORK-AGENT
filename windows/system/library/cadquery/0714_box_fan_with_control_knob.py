# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, box_fan_with_control_knob, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: box_fan_with_control_knob

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

def _extrude_profile(points, height, *, center=True, z0=None):
    """Extrude a closed 2D profile (XY) by height along +Z. Returns cq.Solid."""
    pts = _ensure_ccw(_profile_points_2d(points))
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for (x, y) in pts], close=True))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, float(height)))
    dz = (-height / 2.0 if center else 0.0) if z0 is None else z0
    if dz:
        solid = solid.translate(cq.Vector(0, 0, dz))
    return solid

# ===== brackets_hinges_bezels (1 syms) =====
_EPS = 1e-9

# ===== lathe_extrude_loft (2 syms) =====
def _loft_side_faces(rings, closed):
    """Ruled side-wall faces between consecutive 3D rings (matched point counts).
    Each quad is split into two planar triangles, matching the sdk mesh exactly."""
    faces = []
    ring_count = len(rings[0])
    seg = ring_count if closed else ring_count - 1
    for i in range(len(rings) - 1):
        a_ring = rings[i]
        b_ring = rings[i + 1]
        for j in range(seg):
            j2 = (j + 1) % ring_count
            quad = (a_ring[j], a_ring[j2], b_ring[j2], b_ring[j])
            for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
                if (tri[0] == tri[1] or tri[1] == tri[2] or tri[2] == tri[0]):
                    continue
                try:
                    w = cq.Wire.makePolygon([cq.Vector(*p) for p in tri], close=True)
                    faces.append(cq.Face.makeFromWires(w))
                except Exception:
                    continue
    return faces

class ExtrudeGeometry(MeshGeometry):
    """Extrude a 2D profile by `height` along +Z. center=True -> z in
    [-h/2, h/2]; center=False -> z in [0, h]."""

    @classmethod
    def centered(cls, profile, height, *, cap=True, closed=True):
        return cls(profile, height, cap=cap, center=True, closed=closed)

    @classmethod
    def from_z0(cls, profile, height, *, cap=True, closed=True):
        return cls(profile, height, cap=cap, center=False, closed=closed)

    def __init__(self, profile, height, *, cap=True, center=True, closed=True):
        super().__init__()
        height = float(height)
        if height <= 0:
            raise ValidationError("Extrude height must be positive")

        points = _ensure_ccw(_profile_points_2d(profile))
        if not closed:
            cap = False

        if cap:
            self._set(_extrude_profile(points, height, center=center))
            return

        z0 = -height / 2.0 if center else 0.0
        z1 = z0 + height
        rings = [[(x, y, z0) for (x, y) in points], [(x, y, z1) for (x, y) in points]]
        faces = _loft_side_faces(rings, closed)
        if not faces:
            raise ValidationError("Extrude produced no valid side faces")
        self._set(cq.Shell.makeShell(faces))

# ===== primitives (1 syms) =====
class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

# ===== sweeps (23 syms) =====
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
ASSETS = AssetContext.from_script(__file__)
def _save_mesh(name: str, geometry):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(name))
def _midpoint(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)
def _rpy_for_cylinder(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    length_xy = math.hypot(dx, dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(length_xy, dz)
    return (0.0, pitch, yaw)
def _add_member(part, name: str, a, b, radius: float, material) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_cylinder(a, b)),
        material=material,
        name=name,
    )
def _build_blade_mesh():
    profile = [
        (0.024, -0.014),
        (0.050, -0.030),
        (0.100, -0.032),
        (0.142, -0.015),
        (0.150, 0.010),
        (0.128, 0.028),
        (0.084, 0.034),
        (0.046, 0.024),
        (0.024, 0.010),
    ]
    return _save_mesh("box_fan_blade.obj", ExtrudeGeometry(profile, height=0.006, center=True))
def _build_square_grille_loop():
    return _save_mesh(
        "box_fan_grille_square_loop.obj",
        wire_from_points(
            [
                (-0.164, 0.0, -0.164),
                (0.164, 0.0, -0.164),
                (0.164, 0.0, 0.164),
                (-0.164, 0.0, 0.164),
            ],
            radius=0.004,
            radial_segments=14,
            closed_path=True,
            corner_mode="fillet",
            corner_radius=0.020,
            corner_segments=8,
        ),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="square_box_fan", assets=ASSETS)

    housing_white = model.material("housing_white", rgba=(0.88, 0.89, 0.91, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.62, 0.66, 0.70, 1.0))
    grille_dark = model.material("grille_dark", rgba=(0.26, 0.29, 0.31, 1.0))
    blade_gray = model.material("blade_gray", rgba=(0.76, 0.79, 0.82, 1.0))
    hub_gray = model.material("hub_gray", rgba=(0.56, 0.60, 0.64, 1.0))
    knob_black = model.material("knob_black", rgba=(0.10, 0.11, 0.12, 1.0))

    blade_mesh = _build_blade_mesh()
    square_loop_mesh = _build_square_grille_loop()
    ring_meshes = {
        "ring_inner": _save_mesh("box_fan_grille_ring_inner.obj", TorusGeometry(radius=0.048, tube=0.0034)),
        "ring_mid_1": _save_mesh("box_fan_grille_ring_mid_1.obj", TorusGeometry(radius=0.082, tube=0.0034)),
        "ring_mid_2": _save_mesh("box_fan_grille_ring_mid_2.obj", TorusGeometry(radius=0.116, tube=0.0034)),
        "ring_outer": _save_mesh("box_fan_grille_ring_outer.obj", TorusGeometry(radius=0.156, tube=0.0034)),
    }

    width = 0.42
    height = 0.42
    depth = 0.11
    border = 0.045
    opening = width - (2.0 * border)
    half_w = width * 0.5
    half_h = height * 0.5
    half_d = depth * 0.5
    front_bezel_depth = 0.012

    housing = model.part("housing")
    housing.visual(
        Box((width, depth, border)),
        origin=Origin(xyz=(0.0, 0.0, half_h - (border * 0.5))),
        material=housing_white,
        name="top_shell",
    )
    housing.visual(
        Box((width, depth, border)),
        origin=Origin(xyz=(0.0, 0.0, -half_h + (border * 0.5))),
        material=housing_white,
        name="bottom_shell",
    )
    housing.visual(
        Box((border, depth, opening)),
        origin=Origin(xyz=(-half_w + (border * 0.5), 0.0, 0.0)),
        material=housing_white,
        name="left_shell",
    )
    housing.visual(
        Box((border, depth, opening)),
        origin=Origin(xyz=(half_w - (border * 0.5), 0.0, 0.0)),
        material=housing_white,
        name="right_shell",
    )
    housing.visual(
        Box((width - 0.006, front_bezel_depth, border + 0.012)),
        origin=Origin(xyz=(0.0, half_d - (front_bezel_depth * 0.5), half_h - (border + 0.012) * 0.5)),
        material=trim_gray,
        name="front_top_bezel",
    )
    housing.visual(
        Box((width - 0.006, front_bezel_depth, border + 0.012)),
        origin=Origin(xyz=(0.0, half_d - (front_bezel_depth * 0.5), -half_h + (border + 0.012) * 0.5)),
        material=trim_gray,
        name="front_bottom_bezel",
    )
    housing.visual(
        Box((border + 0.012, front_bezel_depth, opening + 0.016)),
        origin=Origin(xyz=(-half_w + (border + 0.012) * 0.5, half_d - (front_bezel_depth * 0.5), 0.0)),
        material=trim_gray,
        name="front_left_bezel",
    )
    housing.visual(
        Box((border + 0.012, front_bezel_depth, opening + 0.016)),
        origin=Origin(xyz=(half_w - (border + 0.012) * 0.5, half_d - (front_bezel_depth * 0.5), 0.0)),
        material=trim_gray,
        name="front_right_bezel",
    )
    housing.visual(
        Box((opening, 0.016, 0.022)),
        origin=Origin(xyz=(0.0, -0.020, 0.0)),
        material=trim_gray,
        name="motor_crossbar_horizontal",
    )
    housing.visual(
        Box((0.022, 0.016, opening)),
        origin=Origin(xyz=(0.0, -0.020, 0.0)),
        material=trim_gray,
        name="motor_crossbar_vertical",
    )
    housing.visual(
        Cylinder(radius=0.055, length=0.045),
        origin=Origin(xyz=(0.0, -0.010, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_gray,
        name="motor_pod",
    )
    housing.visual(
        Cylinder(radius=0.010, length=0.114),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hub_gray,
        name="center_spindle",
    )
    housing.visual(
        Cylinder(radius=0.030, length=0.008),
        origin=Origin(xyz=(half_w + 0.004, 0.0, -0.100), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_gray,
        name="control_boss",
    )
    housing.inertial = Inertial.from_geometry(
        Box((width, depth, height)),
        mass=2.4,
        origin=Origin(),
    )

    front_grille = model.part("front_grille")
    front_grille.visual(
        square_loop_mesh,
        origin=Origin(),
        material=grille_dark,
        name="square_loop",
    )
    for ring_name, ring_mesh in ring_meshes.items():
        front_grille.visual(
            ring_mesh,
            origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=grille_dark,
            name=ring_name,
        )
    spoke_angles = (
        0.0,
        math.pi * 0.25,
        math.pi * 0.5,
        math.pi * 0.75,
        math.pi,
        math.pi * 1.25,
        math.pi * 1.5,
        math.pi * 1.75,
    )
    for index, angle in enumerate(spoke_angles):
        radius = 0.162
        end = (math.cos(angle) * radius, 0.0, math.sin(angle) * radius)
        _add_member(front_grille, f"spoke_{index}", (0.0, 0.0, 0.0), end, 0.003, grille_dark)
    front_grille.visual(
        Box((0.018, 0.014, 0.020)),
        origin=Origin(xyz=(0.156, -0.007, 0.0)),
        material=grille_dark,
        name="tab_right",
    )
    front_grille.visual(
        Box((0.018, 0.014, 0.020)),
        origin=Origin(xyz=(-0.156, -0.007, 0.0)),
        material=grille_dark,
        name="tab_left",
    )
    front_grille.visual(
        Box((0.020, 0.014, 0.018)),
        origin=Origin(xyz=(0.0, -0.007, 0.156)),
        material=grille_dark,
        name="tab_top",
    )
    front_grille.visual(
        Box((0.020, 0.014, 0.018)),
        origin=Origin(xyz=(0.0, -0.007, -0.156)),
        material=grille_dark,
        name="tab_bottom",
    )
    front_grille.inertial = Inertial.from_geometry(
        Box((0.34, 0.016, 0.34)),
        mass=0.2,
        origin=Origin(),
    )

    rotor = model.part("rotor")
    rotor.visual(
        Cylinder(radius=0.034, length=0.052),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hub_gray,
        name="hub_sleeve",
    )
    rotor.visual(
        Cylinder(radius=0.024, length=0.020),
        origin=Origin(xyz=(0.0, 0.016, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hub_gray,
        name="front_cap",
    )
    blade_count = 5
    for index in range(blade_count):
        angle = (2.0 * math.pi * index) / blade_count
        rotor.visual(
            blade_mesh,
            origin=Origin(rpy=(math.pi / 2.0, angle, 0.0)),
            material=blade_gray,
            name=f"blade_{index}",
        )
    rotor.inertial = Inertial.from_geometry(
        Box((0.32, 0.055, 0.32)),
        mass=0.35,
        origin=Origin(),
    )

    knob = model.part("speed_knob")
    knob.visual(
        Cylinder(radius=0.022, length=0.028),
        origin=Origin(xyz=(0.014, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=knob_black,
        name="knob_body",
    )
    knob.visual(
        Cylinder(radius=0.010, length=0.010),
        origin=Origin(xyz=(0.005, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=hub_gray,
        name="knob_stem",
    )
    knob.visual(
        Box((0.010, 0.003, 0.010)),
        origin=Origin(xyz=(0.027, 0.0, 0.016)),
        material=housing_white,
        name="indicator_tick",
    )
    knob.inertial = Inertial.from_geometry(
        Box((0.040, 0.045, 0.045)),
        mass=0.05,
        origin=Origin(xyz=(0.020, 0.0, 0.0)),
    )

    model.articulation(
        "grille_mount",
        ArticulationType.FIXED,
        parent="housing",
        child="front_grille",
        origin=Origin(xyz=(0.0, half_d + 0.001, 0.0)),
    )
    model.articulation(
        "blade_spin",
        ArticulationType.CONTINUOUS,
        parent="housing",
        child="rotor",
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=22.0),
    )
    model.articulation(
        "speed_control",
        ArticulationType.CONTINUOUS,
        parent="housing",
        child="speed_knob",
        origin=Origin(xyz=(half_w + 0.008, 0.0, -0.100)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.2, velocity=8.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
