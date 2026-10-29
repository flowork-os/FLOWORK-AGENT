# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="solar_observation_refractor")

    tripod_metal = model.material("tripod_metal", rgba=(0.26, 0.28, 0.31, 1.0))
    carbon_fiber = model.material("carbon_fiber", rgba=(0.12, 0.14, 0.16, 1.0))
    rubber = model.material("rubber", rgba=(0.10, 0.10, 0.11, 1.0))
    head_gray = model.material("head_gray", rgba=(0.74, 0.76, 0.79, 1.0))
    head_dark = model.material("head_dark", rgba=(0.21, 0.23, 0.25, 1.0))
    tube_white = model.material("tube_white", rgba=(0.95, 0.95, 0.93, 1.0))
    trim_black = model.material("trim_black", rgba=(0.08, 0.09, 0.10, 1.0))
    anodized_red = model.material("anodized_red", rgba=(0.69, 0.14, 0.10, 1.0))
    solar_filter = model.material("solar_filter", rgba=(0.78, 0.46, 0.12, 0.72))

    def x_axis_origin(
        xyz: tuple[float, float, float],
        *,
        extra_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> Origin:
        return Origin(
            xyz=xyz,
            rpy=(
                extra_rpy[0],
                extra_rpy[1] + (math.pi / 2.0),
                extra_rpy[2],
            ),
        )

    def y_axis_origin(
        xyz: tuple[float, float, float],
        *,
        extra_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> Origin:
        return Origin(
            xyz=xyz,
            rpy=(
                extra_rpy[0] + (math.pi / 2.0),
                extra_rpy[1],
                extra_rpy[2],
            ),
        )

    main_tube_mesh = mesh_from_geometry(
        LatheGeometry.from_shell_profiles(
            outer_profile=((0.046, -0.26), (0.046, 0.26)),
            inner_profile=((0.041, -0.255), (0.041, 0.255)),
            segments=64,
        ),
        "refractor_main_tube",
    )
    dew_shield_mesh = mesh_from_geometry(
        LatheGeometry.from_shell_profiles(
            outer_profile=((0.057, -0.09), (0.057, 0.09)),
            inner_profile=((0.052, -0.085), (0.052, 0.085)),
            segments=64,
        ),
        "refractor_dew_shield",
    )

    tripod_center = model.part("tripod_center")
    tripod_center.visual(
        Cylinder(radius=0.055, length=0.09),
        origin=Origin(xyz=(0.0, 0.0, 1.015)),
        material=tripod_metal,
        name="tripod_crown",
    )
    tripod_center.visual(
        Cylinder(radius=0.092, length=0.02),
        origin=Origin(xyz=(0.0, 0.0, 1.068)),
        material=head_dark,
        name="azimuth_seat",
    )
    tripod_center.visual(
        Cylinder(radius=0.022, length=0.44),
        origin=Origin(xyz=(0.0, 0.0, 0.80)),
        material=tripod_metal,
        name="spreader_column",
    )
    tripod_center.visual(
        Cylinder(radius=0.05, length=0.045),
        origin=Origin(xyz=(0.0, 0.0, 0.575)),
        material=tripod_metal,
        name="tray_hub",
    )
    for index in range(3):
        angle = index * (2.0 * math.pi / 3.0)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        tripod_center.visual(
            Box((0.09, 0.046, 0.045)),
            origin=Origin(
                xyz=(0.07 * cos_a, 0.07 * sin_a, 0.968),
                rpy=(0.0, 0.0, angle),
            ),
            material=tripod_metal,
            name=f"leg_socket_{index}",
        )
        tripod_center.visual(
            Box((0.22, 0.05, 0.008)),
            origin=Origin(
                xyz=(0.15 * cos_a, 0.15 * sin_a, 0.60),
                rpy=(0.0, 0.0, angle),
            ),
            material=tripod_metal,
            name=f"tray_arm_{index}",
        )
    tripod_center.inertial = Inertial.from_geometry(
        Box((0.28, 0.28, 1.11)),
        mass=2.8,
        origin=Origin(xyz=(0.0, 0.0, 0.555)),
    )

    for index in range(3):
        leg = model.part(f"leg_{index}")
        leg.visual(
            Cylinder(radius=0.019, length=0.06),
            origin=Origin(xyz=(0.0, 0.0, 0.03)),
            material=tripod_metal,
            name="top_ferrule",
        )
        leg.visual(
            Cylinder(radius=0.019, length=0.58),
            origin=Origin(xyz=(0.0, 0.0, -0.29)),
            material=carbon_fiber,
            name="upper_tube",
        )
        leg.visual(
            Cylinder(radius=0.014, length=0.52),
            origin=Origin(xyz=(0.0, 0.0, -0.75)),
            material=carbon_fiber,
            name="lower_tube",
        )
        leg.visual(
            Cylinder(radius=0.026, length=0.055),
            origin=Origin(xyz=(0.0, 0.0, -0.485)),
            material=tripod_metal,
            name="leg_clamp",
        )
        leg.visual(
            Sphere(radius=0.03),
            origin=Origin(xyz=(0.0, 0.0, -1.024)),
            material=rubber,
            name="foot_pad",
        )
        leg.inertial = Inertial.from_geometry(
            Box((0.07, 0.07, 1.12)),
            mass=0.72,
            origin=Origin(xyz=(0.0, 0.0, -0.50)),
        )

        leg_angle = index * (2.0 * math.pi / 3.0)
        model.articulation(
            f"tripod_center_to_leg_{index}",
            ArticulationType.FIXED,
            parent=tripod_center,
            child=leg,
            origin=Origin(
                xyz=(0.07 * math.cos(leg_angle), 0.07 * math.sin(leg_angle), 0.968),
                rpy=(0.0, -math.radians(25.0), leg_angle),
            ),
        )

    head = model.part("head")
    head.visual(
        Cylinder(radius=0.094, length=0.02),
        origin=Origin(xyz=(0.0, 0.0, 0.01)),
        material=head_dark,
        name="turntable_plate",
    )
    head.visual(
        Cylinder(radius=0.076, length=0.06),
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        material=head_gray,
        name="azimuth_drum",
    )
    head.visual(
        Box((0.09, 0.085, 0.12)),
        origin=Origin(xyz=(0.0, 0.0, 0.125)),
        material=head_gray,
        name="center_column",
    )
    head.visual(
        Box((0.14, 0.125, 0.03)),
        origin=Origin(xyz=(0.0, 0.0, 0.18)),
        material=head_gray,
        name="yoke_base",
    )
    head.visual(
        Box((0.12, 0.024, 0.18)),
        origin=Origin(xyz=(0.0, 0.07, 0.25)),
        material=head_gray,
        name="left_arm",
    )
    head.visual(
        Box((0.12, 0.024, 0.18)),
        origin=Origin(xyz=(0.0, -0.07, 0.25)),
        material=head_gray,
        name="right_arm",
    )
    head.visual(
        Box((0.05, 0.14, 0.036)),
        origin=Origin(xyz=(-0.04, 0.0, 0.147)),
        material=head_dark,
        name="rear_brace",
    )
    head.visual(
        Cylinder(radius=0.04, length=0.022),
        origin=y_axis_origin((0.0, 0.069, 0.25)),
        material=head_dark,
        name="left_altitude_bearing",
    )
    head.visual(
        Cylinder(radius=0.04, length=0.022),
        origin=y_axis_origin((0.0, -0.069, 0.25)),
        material=head_dark,
        name="right_altitude_bearing",
    )
    head.visual(
        Box((0.055, 0.05, 0.045)),
        origin=Origin(xyz=(-0.02, 0.091, 0.205)),
        material=head_dark,
        name="altitude_control_housing",
    )
    head.visual(
        Box((0.04, 0.06, 0.04)),
        origin=Origin(xyz=(0.09, 0.0, 0.07)),
        material=head_dark,
        name="azimuth_control_housing",
    )
    head.inertial = Inertial.from_geometry(
        Box((0.22, 0.19, 0.36)),
        mass=2.9,
        origin=Origin(xyz=(0.0, 0.0, 0.18)),
    )

    optical_tube = model.part("optical_tube")
    optical_tube.visual(
        main_tube_mesh,
        origin=x_axis_origin((0.04, 0.0, 0.0)),
        material=tube_white,
        name="main_tube_shell",
    )
    optical_tube.visual(
        dew_shield_mesh,
        origin=x_axis_origin((0.35, 0.0, 0.0)),
        material=trim_black,
        name="dew_shield_shell",
    )
    optical_tube.visual(
        Cylinder(radius=0.052, length=0.09),
        origin=x_axis_origin((0.315, 0.0, 0.0)),
        material=trim_black,
        name="front_coupling_sleeve",
    )
    optical_tube.visual(
        Cylinder(radius=0.062, length=0.04),
        origin=x_axis_origin((0.445, 0.0, 0.0)),
        material=anodized_red,
        name="objective_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.056, length=0.008),
        origin=x_axis_origin((0.466, 0.0, 0.0)),
        material=solar_filter,
        name="front_filter",
    )
    optical_tube.visual(
        Cylinder(radius=0.05, length=0.06),
        origin=x_axis_origin((-0.25, 0.0, 0.0)),
        material=trim_black,
        name="rear_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.033, length=0.10),
        origin=x_axis_origin((-0.33, 0.0, 0.0)),
        material=trim_black,
        name="focuser_body",
    )
    optical_tube.visual(
        Cylinder(radius=0.02, length=0.10),
        origin=x_axis_origin((-0.43, 0.0, 0.0)),
        material=head_gray,
        name="drawtube",
    )
    optical_tube.visual(
        Cylinder(radius=0.017, length=0.04),
        origin=x_axis_origin((-0.50, 0.0, 0.0)),
        material=trim_black,
        name="diagonal_nosepiece",
    )
    optical_tube.visual(
        Box((0.045, 0.032, 0.055)),
        origin=Origin(xyz=(-0.54, 0.0, 0.012), rpy=(0.0, math.radians(40.0), 0.0)),
        material=trim_black,
        name="diagonal_body",
    )
    optical_tube.visual(
        Cylinder(radius=0.014, length=0.08),
        origin=Origin(xyz=(-0.565, 0.0, 0.04)),
        material=head_gray,
        name="eyepiece_barrel",
    )
    optical_tube.visual(
        Cylinder(radius=0.018, length=0.03),
        origin=Origin(xyz=(-0.565, 0.0, 0.095)),
        material=rubber,
        name="eyecup",
    )
    optical_tube.visual(
        Cylinder(radius=0.055, length=0.018),
        origin=x_axis_origin((-0.05, 0.0, 0.0)),
        material=head_dark,
        name="rear_tube_ring",
    )
    optical_tube.visual(
        Cylinder(radius=0.055, length=0.018),
        origin=x_axis_origin((0.055, 0.0, 0.0)),
        material=head_dark,
        name="front_tube_ring",
    )
    optical_tube.visual(
        Box((0.14, 0.082, 0.072)),
        origin=Origin(xyz=(0.0, 0.0, -0.002)),
        material=head_dark,
        name="mounting_cradle",
    )
    optical_tube.visual(
        Cylinder(radius=0.038, length=0.024),
        origin=y_axis_origin((0.0, 0.046, 0.0)),
        material=head_dark,
        name="left_trunnion",
    )
    optical_tube.visual(
        Cylinder(radius=0.038, length=0.024),
        origin=y_axis_origin((0.0, -0.046, 0.0)),
        material=head_dark,
        name="right_trunnion",
    )
    optical_tube.inertial = Inertial.from_geometry(
        Box((0.80, 0.14, 0.18)),
        mass=2.3,
        origin=Origin(xyz=(0.04, 0.0, 0.0)),
    )

    altitude_knob = model.part("altitude_knob")
    altitude_knob.visual(
        Cylinder(radius=0.01, length=0.006),
        origin=y_axis_origin((0.0, 0.003, 0.0)),
        material=head_dark,
        name="collar",
    )
    altitude_knob.visual(
        Cylinder(radius=0.018, length=0.014),
        origin=y_axis_origin((0.0, 0.013, 0.0)),
        material=head_dark,
        name="knob_body",
    )
    altitude_knob.visual(
        Cylinder(radius=0.003, length=0.026),
        origin=x_axis_origin((0.0, 0.018, 0.014)),
        material=head_gray,
        name="knob_handle",
    )
    altitude_knob.inertial = Inertial.from_geometry(
        Box((0.03, 0.03, 0.04)),
        mass=0.05,
        origin=Origin(xyz=(0.0, 0.014, 0.0)),
    )

    azimuth_knob = model.part("azimuth_knob")
    azimuth_knob.visual(
        Cylinder(radius=0.01, length=0.006),
        origin=x_axis_origin((0.003, 0.0, 0.0)),
        material=head_dark,
        name="collar",
    )
    azimuth_knob.visual(
        Cylinder(radius=0.02, length=0.014),
        origin=x_axis_origin((0.013, 0.0, 0.0)),
        material=head_dark,
        name="knob_body",
    )
    azimuth_knob.visual(
        Cylinder(radius=0.003, length=0.03),
        origin=Origin(xyz=(0.018, 0.015, 0.0)),
        material=head_gray,
        name="knob_handle",
    )
    azimuth_knob.inertial = Inertial.from_geometry(
        Box((0.04, 0.04, 0.04)),
        mass=0.05,
        origin=Origin(xyz=(0.014, 0.0, 0.0)),
    )

    model.articulation(
        "head_azimuth",
        ArticulationType.REVOLUTE,
        parent=tripod_center,
        child=head,
        origin=Origin(xyz=(0.0, 0.0, 1.078)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.2,
            lower=-math.radians(170.0),
            upper=math.radians(170.0),
        ),
    )
    model.articulation(
        "tube_altitude",
        ArticulationType.REVOLUTE,
        parent=head,
        child=optical_tube,
        origin=Origin(xyz=(0.0, 0.0, 0.25)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=16.0,
            velocity=1.0,
            lower=0.0,
            upper=math.radians(88.0),
        ),
    )
    model.articulation(
        "altitude_fine_adjust",
        ArticulationType.REVOLUTE,
        parent=head,
        child=altitude_knob,
        origin=Origin(xyz=(-0.02, 0.116, 0.205)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.4,
            velocity=12.0,
            lower=-6.0 * math.pi,
            upper=6.0 * math.pi,
        ),
    )
    model.articulation(
        "azimuth_fine_adjust",
        ArticulationType.REVOLUTE,
        parent=head,
        child=azimuth_knob,
        origin=Origin(xyz=(0.11, 0.0, 0.07)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.4,
            velocity=12.0,
            lower=-6.0 * math.pi,
            upper=6.0 * math.pi,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
