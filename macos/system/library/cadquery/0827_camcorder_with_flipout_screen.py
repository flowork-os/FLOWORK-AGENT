# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camcorder_with_flipout_screen, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camcorder_with_flipout_screen

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
PI_2 = math.pi / 2.0
def _tube_mesh(name: str, outer_radius: float, inner_radius: float, length: float):
    """A simple hollow revolved tube, authored on local Z."""
    return mesh_from_geometry(
        LatheGeometry.from_shell_profiles(
            [(outer_radius, -length / 2.0), (outer_radius, length / 2.0)],
            [(inner_radius, -length / 2.0), (inner_radius, length / 2.0)],
            segments=72,
            start_cap="flat",
            end_cap="flat",
        ),
        name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="professional_shoulder_camcorder")

    mat_body = model.material("satin_black", rgba=(0.015, 0.017, 0.020, 1.0))
    mat_panel = model.material("dark_graphite", rgba=(0.055, 0.060, 0.066, 1.0))
    mat_rubber = model.material("matte_rubber", rgba=(0.003, 0.003, 0.004, 1.0))
    mat_lens = model.material("coated_glass", rgba=(0.08, 0.14, 0.20, 0.78))
    mat_screen = model.material("blue_black_screen", rgba=(0.02, 0.045, 0.075, 1.0))
    mat_metal = model.material("hinge_metal", rgba=(0.26, 0.27, 0.28, 1.0))
    mat_red = model.material("record_red", rgba=(0.75, 0.025, 0.02, 1.0))
    mat_label = model.material("white_marking", rgba=(0.86, 0.88, 0.82, 1.0))

    body = model.part("body")
    # Main boxy shoulder-camcorder chassis, about a real ENG-style hand/shoulder scale.
    body.visual(
        Box((0.42, 0.16, 0.18)),
        origin=Origin(xyz=(0.0, 0.0, 0.09)),
        material=mat_body,
        name="main_shell",
    )
    body.visual(
        Box((0.23, 0.115, 0.030)),
        origin=Origin(xyz=(-0.03, 0.0, 0.222)),
        material=mat_body,
        name="top_handle_grip",
    )
    for idx, x in enumerate((-0.125, 0.055)):
        body.visual(
            Box((0.040, 0.040, 0.090)),
            origin=Origin(xyz=(x, 0.0, 0.205)),
            material=mat_body,
            name=f"handle_post_{idx}",
        )
    body.visual(
        Box((0.25, 0.125, 0.025)),
        origin=Origin(xyz=(-0.035, 0.0, -0.0125)),
        material=mat_rubber,
        name="shoulder_pad",
    )

    # Front lens stack: fixed collars and barrel support the rotating focus ring.
    body.visual(
        Cylinder(radius=0.074, length=0.030),
        origin=Origin(xyz=(0.205, 0.0, 0.105), rpy=(0.0, PI_2, 0.0)),
        material=mat_panel,
        name="lens_mount_collar",
    )
    body.visual(
        Cylinder(radius=0.052, length=0.270),
        origin=Origin(xyz=(0.325, 0.0, 0.105), rpy=(0.0, PI_2, 0.0)),
        material=mat_body,
        name="lens_barrel",
    )
    for idx, x in enumerate((0.265, 0.337)):
        body.visual(
            Cylinder(radius=0.057, length=0.014),
            origin=Origin(xyz=(x, 0.0, 0.105), rpy=(0.0, PI_2, 0.0)),
            material=mat_panel,
            name=f"ring_stop_{idx}",
        )
    body.visual(
        Cylinder(radius=0.047, length=0.060),
        origin=Origin(xyz=(0.455, 0.0, 0.105), rpy=(0.0, PI_2, 0.0)),
        material=mat_rubber,
        name="front_lens_hood",
    )
    body.visual(
        Cylinder(radius=0.039, length=0.006),
        origin=Origin(xyz=(0.427, 0.0, 0.105), rpy=(0.0, PI_2, 0.0)),
        material=mat_lens,
        name="front_glass",
    )

    # Rear viewfinder/eyepiece with a rubber eyecup.
    body.visual(
        Box((0.045, 0.055, 0.045)),
        origin=Origin(xyz=(-0.205, 0.0, 0.135)),
        material=mat_panel,
        name="viewfinder_block",
    )
    body.visual(
        Cylinder(radius=0.027, length=0.085),
        origin=Origin(xyz=(-0.248, 0.0, 0.135), rpy=(0.0, PI_2, 0.0)),
        material=mat_body,
        name="eyepiece_tube",
    )
    body.visual(
        Cylinder(radius=0.035, length=0.026),
        origin=Origin(xyz=(-0.303, 0.0, 0.135), rpy=(0.0, PI_2, 0.0)),
        material=mat_rubber,
        name="rubber_eyecup",
    )

    # LCD side hinge fixed leaves and knuckles on the left side of the body.
    body.visual(
        Box((0.034, 0.006, 0.122)),
        origin=Origin(xyz=(-0.062, 0.083, 0.095)),
        material=mat_metal,
        name="lcd_hinge_leaf",
    )
    for idx, z in enumerate((0.056, 0.134)):
        body.visual(
            Cylinder(radius=0.008, length=0.028),
            origin=Origin(xyz=(-0.062, 0.089, z)),
            material=mat_metal,
            name=f"lcd_fixed_knuckle_{idx}",
        )

    # Media-door fixed hinge support on the right side.
    body.visual(
        Box((0.018, 0.006, 0.112)),
        origin=Origin(xyz=(0.155, -0.083, 0.090)),
        material=mat_metal,
        name="door_hinge_leaf",
    )
    for idx, z in enumerate((0.054, 0.126)):
        body.visual(
            Cylinder(radius=0.006, length=0.026),
            origin=Origin(xyz=(0.155, -0.089, z)),
            material=mat_metal,
            name=f"door_fixed_knuckle_{idx}",
        )

    # Surface-mounted top control cradle.
    body.visual(
        Box((0.125, 0.050, 0.006)),
        origin=Origin(xyz=(0.010, -0.036, 0.183)),
        material=mat_panel,
        name="top_control_panel",
    )
    for idx, y in enumerate((-0.060, -0.012)):
        body.visual(
            Box((0.070, 0.006, 0.012)),
            origin=Origin(xyz=(0.010, y, 0.192)),
            material=mat_panel,
            name=f"rocker_rail_{idx}",
        )

    # Flip-out LCD first moving stage: a supported hinge arm with a distal yoke.
    lcd_arm = model.part("lcd_arm")
    lcd_arm.visual(
        Cylinder(radius=0.007, length=0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=mat_metal,
        name="swing_knuckle",
    )
    lcd_arm.visual(
        Box((0.112, 0.014, 0.018)),
        origin=Origin(xyz=(0.056, 0.008, 0.0)),
        material=mat_panel,
        name="swing_arm_bar",
    )
    for idx, z in enumerate((-0.032, 0.032)):
        lcd_arm.visual(
            Cylinder(radius=0.007, length=0.018),
            origin=Origin(xyz=(0.115, 0.008, z)),
            material=mat_metal,
            name=f"screen_yoke_{idx}",
        )
    lcd_arm.visual(
        Box((0.024, 0.018, 0.082)),
        origin=Origin(xyz=(0.108, 0.023, 0.0)),
        material=mat_panel,
        name="screen_yoke_bridge",
    )

    model.articulation(
        "body_to_lcd_arm",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lcd_arm,
        origin=Origin(xyz=(-0.062, 0.089, 0.095)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=2.0, lower=0.0, upper=1.75),
    )

    # Flip-out LCD second moving stage: screen panel rotating on the arm yoke.
    lcd_panel = model.part("lcd_panel")
    lcd_panel.visual(
        Box((0.136, 0.012, 0.092)),
        origin=Origin(xyz=(0.080, 0.006, 0.0)),
        material=mat_panel,
        name="screen_case",
    )
    lcd_panel.visual(
        Box((0.112, 0.002, 0.064)),
        origin=Origin(xyz=(0.080, 0.013, 0.0)),
        material=mat_screen,
        name="display_glass",
    )
    lcd_panel.visual(
        Cylinder(radius=0.006, length=0.038),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=mat_metal,
        name="panel_pivot_knuckle",
    )
    lcd_panel.visual(
        Box((0.024, 0.008, 0.038)),
        origin=Origin(xyz=(0.006, 0.000, 0.0)),
        material=mat_panel,
        name="panel_hinge_leaf",
    )
    model.articulation(
        "arm_to_lcd_panel",
        ArticulationType.REVOLUTE,
        parent=lcd_arm,
        child=lcd_panel,
        origin=Origin(xyz=(0.115, 0.008, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=2.5, lower=-1.65, upper=1.65),
    )

    # Hinged media-card door, carried by real side knuckles.
    media_door = model.part("media_door")
    media_door.visual(
        Box((0.108, 0.006, 0.086)),
        origin=Origin(xyz=(-0.054, -0.006, 0.0)),
        material=mat_panel,
        name="door_panel",
    )
    media_door.visual(
        Box((0.085, 0.002, 0.052)),
        origin=Origin(xyz=(-0.057, -0.010, 0.0)),
        material=mat_body,
        name="door_recess",
    )
    media_door.visual(
        Cylinder(radius=0.0055, length=0.041),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=mat_metal,
        name="door_moving_knuckle",
    )
    media_door.visual(
        Box((0.014, 0.006, 0.038)),
        origin=Origin(xyz=(-0.006, -0.003, 0.0)),
        material=mat_metal,
        name="door_hinge_leaf",
    )
    model.articulation(
        "body_to_media_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=media_door,
        origin=Origin(xyz=(0.155, -0.089, 0.090)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.2, velocity=1.5, lower=0.0, upper=1.35),
    )

    # Rotating, hollow focus/zoom ring around the front lens, with raised grip ribs.
    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        _tube_mesh("focus_ring_tube", outer_radius=0.061, inner_radius=0.055, length=0.058),
        origin=Origin(rpy=(0.0, PI_2, 0.0)),
        material=mat_rubber,
        name="ring_shell",
    )
    for idx in range(18):
        theta = idx * 2.0 * math.pi / 18.0
        focus_ring.visual(
            Box((0.044, 0.004, 0.007)),
            origin=Origin(
                xyz=(0.0, -0.063 * math.sin(theta), 0.063 * math.cos(theta)),
                rpy=(theta, 0.0, 0.0),
            ),
            material=mat_rubber,
            name=f"ring_grip_{idx}",
        )
    focus_ring.visual(
        Box((0.030, 0.003, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.064)),
        material=mat_label,
        name="ring_index_mark",
    )
    model.articulation(
        "body_to_focus_ring",
        ArticulationType.REVOLUTE,
        parent=body,
        child=focus_ring,
        origin=Origin(xyz=(0.301, 0.0, 0.105)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.6, velocity=5.0, lower=-math.pi, upper=math.pi),
    )

    # User controls are separate supported moving parts, not painted-on lumps.
    zoom_rocker = model.part("zoom_rocker")
    zoom_rocker.visual(
        Box((0.060, 0.030, 0.012)),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=mat_rubber,
        name="rocker_cap",
    )
    model.articulation(
        "body_to_zoom_rocker",
        ArticulationType.REVOLUTE,
        parent=body,
        child=zoom_rocker,
        origin=Origin(xyz=(0.010, -0.036, 0.186)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.25, velocity=2.0, lower=-0.22, upper=0.22),
    )

    record_button = model.part("record_button")
    record_button.visual(
        Cylinder(radius=0.012, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=mat_red,
        name="record_cap",
    )
    model.articulation(
        "body_to_record_button",
        ArticulationType.PRISMATIC,
        parent=body,
        child=record_button,
        origin=Origin(xyz=(-0.035, -0.052, 0.186)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=0.12, velocity=0.06, lower=0.0, upper=0.004),
    )

    for idx, y in enumerate((-0.046, 0.046)):
        button = model.part(f"button_{idx}")
        button.visual(
            Box((0.006, 0.025, 0.015)),
            origin=Origin(xyz=(-0.003, y, 0.055)),
            material=mat_panel,
            name=f"rear_button_cap_{idx}",
        )
        model.articulation(
            f"body_to_button_{idx}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(-0.210, 0.0, 0.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=0.10, velocity=0.05, lower=0.0, upper=0.003),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
