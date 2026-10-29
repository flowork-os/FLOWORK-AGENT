# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cannon, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cannon

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from math import acos, atan2, cos, isfinite, pi, sin, sqrt, tan
from typing import Iterable, List, Optional, Sequence, Tuple, Union
from typing import Literal, Optional, Sequence

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

def _point_in_polygon(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside

def _extrude_profile(points, height, *, center=True, z0=None):
    """Extrude a closed 2D profile (XY) by height along +Z. Returns cq.Solid."""
    pts = _ensure_ccw(_profile_points_2d(points))
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for (x, y) in pts], close=True))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, float(height)))
    dz = (-height / 2.0 if center else 0.0) if z0 is None else z0
    if dz:
        solid = solid.translate(cq.Vector(0, 0, dz))
    return solid

def _revolve_profile(profile_rz, *, angle=360.0):
    """Revolve a closed (r,z) profile about the Z axis. r=radius>=0, z=height.
    Matches Articraft LatheGeometry (profile point (r,z) -> circle of radius r
    at height z)."""
    pts = [(float(r), float(z)) for (r, z) in profile_rz]
    wire = cq.Wire.makePolygon([cq.Vector(r, 0.0, z) for (r, z) in pts], close=True)
    return cq.Solid.revolve(wire, [], float(angle), cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))

# ===== brackets_hinges_bezels (2 syms) =====
_EPS = 1e-9

def _polygon_centroid(points):
    sx = sum(p[0] for p in points)
    sy = sum(p[1] for p in points)
    n = max(1, len(points))
    return (sx / float(n), sy / float(n))

# ===== lathe_extrude_loft (7 syms) =====
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

class ExtrudeWithHolesGeometry(MeshGeometry):
    """Extrude a 2D outer profile minus one or more through-holes."""

    def __init__(self, outer_profile, hole_profiles, height, *, cap=True,
                 center=True, closed=True):
        super().__init__()
        height = float(height)
        if height <= 0:
            raise ValidationError("Extrude height must be positive")

        outer = _ensure_ccw(_profile_points_2d(outer_profile))
        holes = [_ensure_ccw(_profile_points_2d(h)) for h in hole_profiles]
        if not closed:
            cap = False

        for hole in holes:
            c = _polygon_centroid(hole)
            if not _point_in_polygon(c, outer):
                raise ValidationError("Hole profile must lie inside outer profile")

        if not holes:
            self._set(_to_shape(ExtrudeGeometry(outer, height, cap=cap,
                                                center=center, closed=closed)))
            return

        z0 = -height / 2.0 if center else 0.0
        z1 = z0 + height

        if cap:
            outer_wire = cq.Wire.makePolygon(
                [cq.Vector(x, y, 0.0) for (x, y) in outer], close=True)
            hole_wires = [
                cq.Wire.makePolygon([cq.Vector(x, y, 0.0) for (x, y) in h], close=True)
                for h in holes
            ]
            solid = cq.Solid.extrudeLinear(outer_wire, hole_wires, cq.Vector(0, 0, height))
            if z0:
                solid = solid.translate(cq.Vector(0, 0, z0))
            self._set(solid)
            return

        # Open shell: outer side walls + interior (reversed) hole side walls.
        faces = _loft_side_faces(
            [[(x, y, z0) for (x, y) in outer], [(x, y, z1) for (x, y) in outer]], closed)
        for hole in holes:
            hole_cw = list(reversed(hole))
            faces += _loft_side_faces(
                [[(x, y, z0) for (x, y) in hole_cw], [(x, y, z1) for (x, y) in hole_cw]], closed)
        if not faces:
            raise ValidationError("ExtrudeWithHoles produced no valid side faces")
        self._set(cq.Shell.makeShell(faces))

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

# ===== wheels_tires (22 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

def _wheels_tires_clamp(x, low, high):
    return max(low, min(high, x))

def _cq_annulus_x(outer_radius, inner_radius, width):
    return (
        cq.Workplane("YZ")
        .circle(float(outer_radius))
        .circle(max(float(inner_radius), 1.0e-4))
        .extrude(float(width) * 0.5, both=True)
    )

def _wheels_tires_centered_pattern_positions(count, spacing):
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    origin = -0.5 * float(spacing) * float(count - 1)
    return [origin + float(index) * float(spacing) for index in range(count)]

def _wheels_tires_rounded_slot_profile(length, width, *, segments=10):
    radius = width * 0.5
    straight = max(length - width, 0.0)
    half = straight * 0.5
    points = []
    for index in range(segments + 1):
        theta = -pi * 0.5 + pi * (index / float(segments))
        points.append((half + radius * cos(theta), radius * sin(theta)))
    for index in range(segments + 1):
        theta = pi * 0.5 + pi * (index / float(segments))
        points.append((-half + radius * cos(theta), radius * sin(theta)))
    return points

def _wheels_tires_loft_between_radii_z(radii_and_offsets):
    wp = None
    previous_offset = 0.0
    for radius, offset in radii_and_offsets:
        if wp is None:
            wp = cq.Workplane("XY").workplane(offset=offset).circle(radius)
        else:
            wp = wp.workplane(offset=offset - previous_offset).circle(radius)
        previous_offset = offset
    if wp is None:
        raise ValidationError("No loft sections were provided")
    return wp.loft(combine=True, ruled=False)

def _wheels_tires_cut_with_pattern(shape, cutters):
    for cutter in cutters:
        shape = shape.cut(cutter)
    return shape

def _shift_to_x0(shape):
    """Replicate sdk center=False: shift so the body's min X sits on x=0
    (inner mounting side on the origin plane)."""
    xmin = _to_shape(shape).BoundingBox().xmin
    return shape.translate((-xmin, 0.0, 0.0))

@dataclass(frozen=True)
class WheelRim:
    outer_radius: Optional[float] = None
    inner_radius: Optional[float] = None
    flange_height: float = 0.0
    flange_thickness: float = 0.0
    bead_seat_depth: float = 0.0

@dataclass(frozen=True)
class WheelHub:
    radius: float
    width: float
    cap_style: Literal["flat", "domed", "protruding", "recessed"] = "flat"
    bolt_pattern: Optional["BoltPattern"] = None

@dataclass(frozen=True)
class WheelFace:
    dish_depth: float = 0.0
    front_inset: float = 0.0
    rear_inset: float = 0.0
    window_depth: float = 0.0

@dataclass(frozen=True)
class WheelSpokes:
    style: Literal["none", "disc", "solid_slots", "straight", "split_y", "mesh"] = "none"
    count: Optional[int] = None
    thickness: float = 0.0
    window_radius: float = 0.0
    twist_deg: float = 0.0

@dataclass(frozen=True)
class WheelBore:
    style: Literal["round", "keyed", "hex"] = "round"
    diameter: float = 0.0
    key_width: Optional[float] = None

@dataclass(frozen=True)
class TireCarcass:
    crown_radius: Optional[float] = None
    belt_width_ratio: float = 0.34
    sidewall_bulge: float = 0.08

@dataclass(frozen=True)
class TireTread:
    style: Literal["none", "circumferential", "block", "rib", "chevron", "lug"] = "none"
    depth: float = 0.0
    pitch: Optional[float] = None
    count: Optional[int] = None
    angle_deg: float = 0.0
    land_ratio: float = 0.5

@dataclass(frozen=True)
class TireGroove:
    center_offset: float = 0.0
    width: float = 0.0
    depth: float = 0.0

@dataclass(frozen=True)
class TireSidewall:
    style: Literal["flat", "bulged", "square", "rounded"] = "rounded"
    bulge: float = 0.08
    inset_ratio: float = 0.18

@dataclass(frozen=True)
class TireShoulder:
    style: Literal["soft", "square"] = "soft"
    radius: float = 0.0
    width: float = 0.0

class WheelGeometry(MeshGeometry):
    """Build a wheel/rim/hub visual aligned to local X."""

    def __init__(
        self,
        radius: float,
        width: float,
        *,
        rim: Optional[WheelRim] = None,
        hub: Optional[WheelHub] = None,
        face: Optional[WheelFace] = None,
        spokes: Optional[WheelSpokes] = None,
        bore: Optional[WheelBore] = None,
        flange: Optional["WheelFlange"] = None,
        center: bool = True,
    ):
        super().__init__()
        radius = float(radius)
        width = float(width)
        if radius <= 0.0 or width <= 0.0:
            raise ValidationError("radius and width must be positive")

        rim = rim or WheelRim()
        hub = hub or WheelHub(radius=radius * 0.18, width=width * 0.55)
        face = face or WheelFace()
        spokes = spokes or WheelSpokes(style="disc")
        bore = bore or WheelBore(style="round", diameter=max(radius * 0.18, 0.004))

        rim_outer = float(rim.outer_radius) if rim.outer_radius is not None else radius
        rim_inner = float(rim.inner_radius) if rim.inner_radius is not None else radius * 0.68
        if rim_inner <= 0.0 or rim_inner >= rim_outer:
            raise ValidationError("WheelRim.inner_radius must be positive and less than outer_radius")
        if hub.radius <= 0.0 or hub.width <= 0.0 or hub.radius >= rim_inner:
            raise ValidationError("WheelHub dimensions must be positive and fit inside the rim")
        if bore.diameter <= 0.0 or bore.diameter >= hub.radius * 2.0:
            raise ValidationError("WheelBore.diameter must fit inside the hub")

        shape = _cq_annulus_x(rim_outer, rim_inner, width)
        if rim.flange_height > 1e-6 and rim.flange_thickness > 1e-6:
            flange_inner = max(rim_outer - rim.flange_height, rim_inner + 1.0e-4)
            lip = _cq_annulus_x(rim_outer, flange_inner, rim.flange_thickness)
            shape = shape.union(lip.translate((width * 0.5 - rim.flange_thickness * 0.5, 0.0, 0.0)))
            shape = shape.union(
                lip.translate((-(width * 0.5 - rim.flange_thickness * 0.5), 0.0, 0.0))
            )
        if rim.bead_seat_depth > 1e-6:
            seat = _cq_annulus_x(
                rim_outer,
                max(rim_outer - rim.bead_seat_depth, rim_inner + 1.0e-4),
                max(width * 0.22, 0.004),
            )
            shape = shape.cut(seat)

        hub_cyl = cq.Workplane("YZ").circle(hub.radius).extrude(hub.width * 0.5, both=True)
        shape = shape.union(hub_cyl)
        if hub.cap_style == "domed":
            front_cap = (
                _wheels_tires_loft_between_radii_z(
                    [
                        (hub.radius, 0.0),
                        (hub.radius * 0.82, hub.width * 0.12),
                        (hub.radius * 0.30, hub.width * 0.28),
                    ],
                )
                .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
                .translate((hub.width * 0.5, 0.0, 0.0))
            )
            shape = shape.union(front_cap)
        elif hub.cap_style == "protruding":
            cap = cq.Workplane("YZ").circle(hub.radius * 0.82).extrude(max(width * 0.12, 0.003))
            shape = shape.union(cap.translate((hub.width * 0.5, 0.0, 0.0)))
        elif hub.cap_style == "recessed":
            pocket = cq.Workplane("YZ").circle(hub.radius * 0.55).extrude(max(width * 0.10, 0.002))
            shape = shape.cut(
                pocket.translate((hub.width * 0.5 - max(width * 0.10, 0.002), 0.0, 0.0))
            )

        disc_thickness = max(spokes.thickness, width * 0.08, 0.002)
        face_outer_radius = min(
            rim_outer - max(rim.flange_height * 0.25, radius * 0.02),
            rim_inner + (rim_outer - rim_inner) * 0.28 + face.window_depth,
        )
        face_outer_radius = max(face_outer_radius, hub.radius * 1.6)
        front_inset = _wheels_tires_clamp(
            face.front_inset + max(face.dish_depth, 0.0), 0.0, width * 0.5 - disc_thickness * 0.5
        )
        rear_inset = _wheels_tires_clamp(face.rear_inset, 0.0, width * 0.5 - disc_thickness * 0.5)
        disc_inner_radius = max(hub.radius * 0.78, hub.radius - max(disc_thickness * 0.35, 0.0012))
        front_disc = _cq_annulus_x(
            face_outer_radius, disc_inner_radius, disc_thickness
        ).translate((width * 0.5 - front_inset - disc_thickness * 0.5, 0.0, 0.0))
        rear_disc = _cq_annulus_x(
            face_outer_radius, disc_inner_radius, disc_thickness
        ).translate((-(width * 0.5 - rear_inset - disc_thickness * 0.5), 0.0, 0.0))
        shape = shape.union(front_disc).union(rear_disc)

        spoke_style = spokes.style
        if spoke_style not in {"none", "disc"}:
            spoke_count = spokes.count or (6 if spoke_style in {"straight", "solid_slots"} else 5)
            if spoke_count < 2:
                raise ValidationError("WheelSpokes.count must be at least 2")
            window_width = max(
                spokes.window_radius
                if spokes.window_radius > 0.0
                else (rim_outer - hub.radius) * 0.09,
                0.003,
            )
            slot_length = max((face_outer_radius - hub.radius) * 0.75, 0.010)
            cut_width = width + 0.02
            cutters = []

            def radial_slot(angle_deg, center_radius, length, width_local):
                profile = _wheels_tires_rounded_slot_profile(length, width_local)
                slot = (
                    cq.Workplane("YZ")
                    .polyline([(point[1], point[0] + center_radius) for point in profile])
                    .close()
                    .extrude(cut_width * 0.5, both=True)
                    .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
                )
                return slot

            if spoke_style in {"straight", "solid_slots"}:
                for index in range(spoke_count):
                    cutters.append(
                        radial_slot(
                            360.0 * index / float(spoke_count),
                            (hub.radius + face_outer_radius) * 0.5,
                            slot_length,
                            window_width * (1.5 if spoke_style == "solid_slots" else 1.0),
                        )
                    )
            elif spoke_style == "split_y":
                for index in range(spoke_count):
                    base = 360.0 * index / float(spoke_count)
                    cutters.append(
                        radial_slot(
                            base - 10.0,
                            hub.radius + (face_outer_radius - hub.radius) * 0.44,
                            slot_length * 0.55,
                            window_width * 0.85,
                        )
                    )
                    cutters.append(
                        radial_slot(
                            base + 10.0,
                            hub.radius + (face_outer_radius - hub.radius) * 0.64,
                            slot_length * 0.55,
                            window_width * 0.85,
                        )
                    )
            else:
                rows = (
                    hub.radius + (face_outer_radius - hub.radius) * 0.36,
                    hub.radius + (face_outer_radius - hub.radius) * 0.68,
                )
                for row_index, center_radius in enumerate(rows):
                    count = spoke_count * (2 if row_index == 1 else 1)
                    for index in range(count):
                        cutters.append(
                            radial_slot(
                                360.0 * index / float(count)
                                + (180.0 / float(count) if row_index == 1 else 0.0),
                                center_radius,
                                slot_length * (0.30 if row_index == 0 else 0.24),
                                window_width * 0.72,
                            )
                        )
            shape = _wheels_tires_cut_with_pattern(shape, cutters)

        if hub.bolt_pattern is not None:
            pattern = hub.bolt_pattern
            if pattern.count < 2 or pattern.circle_diameter <= 0.0 or pattern.hole_diameter <= 0.0:
                raise ValidationError(
                    "BoltPattern count, circle_diameter, and hole_diameter must be positive"
                )
            bolt_r = pattern.circle_diameter * 0.5
            if bolt_r + pattern.hole_diameter * 0.5 >= hub.radius:
                raise ValidationError("BoltPattern holes must fit inside the hub")
            for index in range(pattern.count):
                angle = 2.0 * pi * index / float(pattern.count)
                hole = (
                    cq.Workplane("YZ")
                    .circle(pattern.hole_diameter * 0.5)
                    .extrude(width + 0.04, both=True)
                    .translate((0.0, bolt_r * cos(angle), bolt_r * sin(angle)))
                )
                shape = shape.cut(hole)

        if bore.style == "round":
            bore_cut = (
                cq.Workplane("YZ").circle(bore.diameter * 0.5).extrude(width + 0.04, both=True)
            )
        elif bore.style == "hex":
            bore_cut = cq.Workplane("YZ").polygon(6, bore.diameter).extrude(width + 0.04, both=True)
        else:
            key_width = bore.key_width or bore.diameter * 0.32
            bore_cut = (
                cq.Workplane("YZ").circle(bore.diameter * 0.5).extrude(width + 0.04, both=True)
            )
            key = cq.Workplane("YZ").box(width + 0.04, key_width, bore.diameter * 0.5)
            bore_cut = bore_cut.union(key.translate((0.0, bore.diameter * 0.25, 0.0)))
        shape = shape.cut(bore_cut)

        if flange is not None:
            if flange.radius <= 0.0 or flange.thickness <= 0.0:
                raise ValidationError("WheelFlange radius and thickness must be positive")
            ring_inner = max(flange.radius - flange.thickness, hub.radius * 1.05)
            ring = _cq_annulus_x(flange.radius, ring_inner, flange.thickness * 0.6)
            bridge_len = max(flange.offset + flange.thickness * 0.6, flange.thickness * 0.8)
            bridge_radial = max(flange.radius - rim_outer + flange.thickness * 0.35, 0.006)
            bridge_thickness = max(flange.thickness * 0.55, 0.0015)
            strut = cq.Workplane("XY").box(bridge_len, bridge_radial, bridge_thickness)
            x_offsets = []
            if flange.side in {"front", "both"}:
                x_offsets.append(width * 0.5 + flange.offset)
            if flange.side in {"rear", "both"}:
                x_offsets.append(-(width * 0.5 + flange.offset))
            for x_offset in x_offsets:
                ring_shape = ring.translate((x_offset, 0.0, 0.0))
                shape = shape.union(ring_shape)
                axial_mid = (
                    (width * 0.5 + x_offset) * 0.5
                    if x_offset >= 0.0
                    else (-(width * 0.5) + x_offset) * 0.5
                )
                radial_mid = (rim_outer + ring_inner) * 0.5
                for angle_deg in (0.0, 90.0, 180.0, 270.0):
                    shape = shape.union(
                        strut.translate((axial_mid, radial_mid, 0.0)).rotate(
                            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg
                        )
                    )

        if not center:
            shape = _shift_to_x0(shape)
        self._set(_to_shape(shape))

class TireGeometry(MeshGeometry):
    """Build a tire aligned to local X."""

    def __init__(
        self,
        outer_radius: float,
        width: float,
        *,
        inner_radius: Optional[float] = None,
        carcass: Optional[TireCarcass] = None,
        tread: Optional[TireTread] = None,
        grooves: Sequence[TireGroove] = (),
        sidewall: Optional[TireSidewall] = None,
        shoulder: Optional[TireShoulder] = None,
        center: bool = True,
    ):
        super().__init__()
        outer_radius = float(outer_radius)
        width = float(width)
        inner_radius = float(inner_radius) if inner_radius is not None else outer_radius * 0.58
        carcass = carcass or TireCarcass()
        tread = tread or TireTread()
        sidewall = sidewall or TireSidewall()
        shoulder = shoulder or TireShoulder()

        if outer_radius <= 0.0 or width <= 0.0 or inner_radius <= 0.0:
            raise ValidationError("outer_radius, width, and inner_radius must be positive")
        if inner_radius >= outer_radius:
            raise ValidationError("inner_radius must be less than outer_radius")
        if tread.depth < 0.0:
            raise ValidationError("TireTread.depth must be non-negative")
        for groove in grooves:
            if groove.width < 0.0 or groove.depth < 0.0:
                raise ValidationError("TireGroove width/depth must be non-negative")

        half_w = width * 0.5
        belt_half = half_w * _wheels_tires_clamp(carcass.belt_width_ratio, 0.12, 0.96)
        shoulder_w = shoulder.width if shoulder.width > 1e-6 else width * 0.11
        side_bulge = max(sidewall.bulge, carcass.sidewall_bulge, 0.0)
        inner_crown = inner_radius * 0.82
        if sidewall.style == "square":
            outer_side = outer_radius
            shoulder_radius = max(
                outer_radius - max(shoulder.radius, tread.depth * 0.5, outer_radius * 0.01),
                inner_radius + 1.0e-4,
            )
        elif sidewall.style == "flat":
            outer_side = max(outer_radius - width * 0.08, inner_radius + 1.0e-4)
            shoulder_radius = outer_radius
        elif sidewall.style == "bulged":
            outer_side = min(outer_radius + side_bulge * width, outer_radius + width * 0.12)
            shoulder_radius = outer_radius
        else:
            outer_side = max(outer_radius - width * 0.04, inner_radius + 1.0e-4)
            shoulder_radius = outer_radius

        profile = [
            (-half_w, inner_radius),
            (-half_w * 0.92, inner_radius),
            (
                -half_w * 0.78,
                max(inner_radius + (outer_side - inner_radius) * 0.28, inner_radius + 1.0e-4),
            ),
            (-(belt_half + shoulder_w), outer_side),
            (-belt_half, shoulder_radius),
            (0.0, outer_radius),
            (belt_half, shoulder_radius),
            (belt_half + shoulder_w, outer_side),
            (
                half_w * 0.78,
                max(inner_radius + (outer_side - inner_radius) * 0.28, inner_radius + 1.0e-4),
            ),
            (half_w * 0.92, inner_radius),
            (half_w, inner_radius),
            (half_w * 0.55, inner_crown),
            (0.0, inner_crown),
            (-half_w * 0.55, inner_crown),
            (-half_w, inner_radius),
        ]
        shape = (
            cq.Workplane("XY")
            .polyline(profile)
            .close()
            .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
        )

        for groove in grooves:
            if groove.width <= 1e-6 or groove.depth <= 1e-6:
                continue
            cutter = (
                cq.Workplane("XY")
                .moveTo(groove.center_offset - groove.width * 0.5, outer_radius - groove.depth)
                .lineTo(groove.center_offset + groove.width * 0.5, outer_radius - groove.depth)
                .lineTo(
                    groove.center_offset + groove.width * 0.5, outer_radius + groove.depth * 1.6
                )
                .lineTo(
                    groove.center_offset - groove.width * 0.5, outer_radius + groove.depth * 1.6
                )
                .close()
                .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
            )
            shape = shape.cut(cutter)

        tread_style = tread.style
        tread_depth = tread.depth
        if tread_style == "circumferential" and tread_depth > 1e-6:
            groove_count = tread.count or 3
            band_positions = _wheels_tires_centered_pattern_positions(
                groove_count, max(tread.pitch or (width * 0.20), width * 0.14)
            )
            for pos in band_positions:
                cutter = (
                    cq.Workplane("XY")
                    .moveTo(pos - width * 0.03, outer_radius - tread_depth)
                    .lineTo(pos + width * 0.03, outer_radius - tread_depth)
                    .lineTo(pos + width * 0.03, outer_radius + tread_depth * 1.4)
                    .lineTo(pos - width * 0.03, outer_radius + tread_depth * 1.4)
                    .close()
                    .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                )
                shape = shape.cut(cutter)
        elif tread_style == "rib" and tread_depth > 1e-6:
            rib_count = tread.count or 3
            rib_positions = _wheels_tires_centered_pattern_positions(
                rib_count, max(tread.pitch or (width * 0.20), width * 0.14)
            )
            for pos in rib_positions:
                rib = (
                    cq.Workplane("XY")
                    .moveTo(pos - width * 0.04, outer_radius)
                    .lineTo(pos + width * 0.04, outer_radius)
                    .lineTo(pos + width * 0.04, outer_radius + tread_depth)
                    .lineTo(pos - width * 0.04, outer_radius + tread_depth)
                    .close()
                    .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                )
                shape = shape.union(rib)
        elif tread_style in {"block", "lug", "chevron"} and tread_depth > 1e-6:
            circ_count = tread.count or (
                12
                if tread_style == "lug"
                else max(
                    14,
                    int(
                        (2.0 * pi * outer_radius) / max(tread.pitch or (width * 0.45), width * 0.24)
                    ),
                )
            )
            axial_rows = (
                [-width * 0.22, width * 0.22]
                if tread_style == "lug"
                else (
                    [-width * 0.22, 0.0, width * 0.22]
                    if tread_style == "block"
                    else [-width * 0.18, width * 0.18]
                )
            )
            tangential = (2.0 * pi * outer_radius / float(circ_count)) * _wheels_tires_clamp(
                tread.land_ratio, 0.18, 0.85
            )
            axial_width = width * (0.14 if tread_style == "lug" else 0.12)
            for row_index, row_x in enumerate(axial_rows):
                for index in range(circ_count):
                    angle_deg = 360.0 * index / float(circ_count) + (
                        180.0 / float(circ_count) if row_index % 2 == 1 else 0.0
                    )
                    if tread_style == "chevron":
                        for sign in (-1.0, 1.0):
                            lug = (
                                cq.Workplane("XY")
                                .box(axial_width, tread_depth * 1.35, tangential * 0.48)
                                .translate(
                                    (
                                        row_x + sign * axial_width * 0.38,
                                        outer_radius + tread_depth * 0.16,
                                        0.0,
                                    )
                                )
                                .rotate(
                                    (0.0, 0.0, 0.0),
                                    (0.0, 1.0, 0.0),
                                    tread.angle_deg * sign
                                    if abs(tread.angle_deg) > 1e-6
                                    else 24.0 * sign,
                                )
                                .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
                            )
                            shape = shape.union(lug)
                    else:
                        lug = (
                            cq.Workplane("XY")
                            .box(
                                axial_width,
                                tread_depth * 1.35,
                                tangential * (0.55 if tread_style == "lug" else 0.42),
                            )
                            .translate((row_x, outer_radius + tread_depth * 0.16, 0.0))
                            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
                        )
                        shape = shape.union(lug)

        if not center:
            shape = _shift_to_x0(shape)
        self._set(_to_shape(shape))

# ===== model =====
import math
AXLE_Z = 0.43
WHEEL_Y = 0.68
WHEEL_RADIUS = 0.43
WHEEL_WIDTH = 0.15
TRUNNION_X = 0.18
TRUNNION_Z = 0.82
TRAIL_HINGE_X = -0.48
TRAIL_HINGE_Y = 0.18
TRAIL_HINGE_Z = 0.32
def _circle_profile(radius: float, segments: int = 40) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos(2.0 * math.pi * index / segments),
            radius * math.sin(2.0 * math.pi * index / segments),
        )
        for index in range(segments)
    ]
def _trunnion_cheek_geometry():
    outer = [(-0.16, -0.14), (0.16, -0.14), (0.16, 0.14), (-0.16, 0.14)]
    hole = _circle_profile(0.086, 48)
    geom = ExtrudeWithHolesGeometry(outer, [hole], 0.035, center=True)
    geom.rotate_x(math.pi / 2.0)
    return geom
def _barrel_geometry():
    outer_profile = [
        (0.145, -0.24),
        (0.145, -0.10),
        (0.116, -0.05),
        (0.100, 0.32),
        (0.091, 0.82),
        (0.118, 0.88),
        (0.118, 1.02),
        (0.087, 1.08),
        (0.083, 1.17),
    ]
    inner_profile = [(0.050, -0.24), (0.050, 1.17)]
    return LatheGeometry.from_shell_profiles(
        outer_profile,
        inner_profile,
        segments=64,
        start_cap="flat",
        end_cap="flat",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mountain_pack_howitzer")

    olive = model.material("olive_drab", rgba=(0.28, 0.34, 0.20, 1.0))
    dark_olive = model.material("dark_olive", rgba=(0.18, 0.23, 0.15, 1.0))
    gunmetal = model.material("gunmetal", rgba=(0.16, 0.17, 0.16, 1.0))
    worn_steel = model.material("worn_steel", rgba=(0.42, 0.43, 0.40, 1.0))
    tire_steel = model.material("dark_steel_tire", rgba=(0.06, 0.065, 0.06, 1.0))
    bore_black = model.material("bore_black", rgba=(0.005, 0.005, 0.004, 1.0))

    carriage = model.part("carriage")
    carriage.visual(
        Cylinder(radius=0.055, length=1.30),
        origin=Origin(xyz=(0.0, 0.0, AXLE_Z), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=worn_steel,
        name="axle",
    )
    carriage.visual(
        Box((0.34, 0.60, 0.16)),
        origin=Origin(xyz=(0.0, 0.0, AXLE_Z)),
        material=olive,
        name="axle_saddle",
    )
    carriage.visual(
        Box((0.88, 0.18, 0.10)),
        origin=Origin(xyz=(-0.40, 0.0, 0.36)),
        material=dark_olive,
        name="rear_drawbar",
    )
    carriage.visual(
        Box((0.12, 0.13, 0.06)),
        origin=Origin(xyz=(-0.615, 0.080, TRAIL_HINGE_Z)),
        material=dark_olive,
        name="trail_hinge_bridge_0",
    )
    carriage.visual(
        Box((0.12, 0.13, 0.06)),
        origin=Origin(xyz=(-0.615, -0.080, TRAIL_HINGE_Z)),
        material=dark_olive,
        name="trail_hinge_bridge_1",
    )
    carriage.visual(
        Box((0.16, 0.08, 0.18)),
        origin=Origin(xyz=(TRAIL_HINGE_X, TRAIL_HINGE_Y, TRAIL_HINGE_Z)),
        material=worn_steel,
        name="trail_hinge_socket_0",
    )
    carriage.visual(
        Box((0.16, 0.08, 0.18)),
        origin=Origin(xyz=(TRAIL_HINGE_X, -TRAIL_HINGE_Y, TRAIL_HINGE_Z)),
        material=worn_steel,
        name="trail_hinge_socket_1",
    )
    for y, visual_name in ((0.245, "cradle_upright_0"), (-0.245, "cradle_upright_1")):
        carriage.visual(
            Box((0.10, 0.060, 0.35)),
            origin=Origin(xyz=(0.04, y, 0.56)),
            material=olive,
            name=visual_name,
        )
    carriage.visual(
        Box((0.56, 0.56, 0.090)),
        origin=Origin(xyz=(0.16, 0.0, 0.615)),
        material=olive,
        name="cradle_crossmember",
    )
    cheek_mesh = mesh_from_geometry(_trunnion_cheek_geometry(), "trunnion_cheek_plate")
    carriage.visual(
        cheek_mesh,
        origin=Origin(xyz=(TRUNNION_X, 0.225, TRUNNION_Z)),
        material=olive,
        name="trunnion_cheek_0",
    )
    carriage.visual(
        cheek_mesh,
        origin=Origin(xyz=(TRUNNION_X, -0.225, TRUNNION_Z)),
        material=olive,
        name="trunnion_cheek_1",
    )
    for y, visual_name in ((0.180, "cradle_rail_0"), (-0.180, "cradle_rail_1")):
        carriage.visual(
            Box((0.60, 0.040, 0.060)),
            origin=Origin(xyz=(0.32, y, 0.685)),
            material=dark_olive,
            name=visual_name,
        )
    carriage.visual(
        Box((0.22, 0.72, 0.030)),
        origin=Origin(xyz=(-0.09, 0.0, 0.565)),
        material=worn_steel,
        name="spring_equalizer",
    )

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_geometry(_barrel_geometry(), "short_hollow_barrel"),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=gunmetal,
        name="barrel_shell",
    )
    barrel.visual(
        Box((0.22, 0.26, 0.23)),
        origin=Origin(xyz=(-0.18, 0.0, 0.0)),
        material=gunmetal,
        name="breech_block",
    )
    barrel.visual(
        Cylinder(radius=0.065, length=0.36),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=worn_steel,
        name="trunnion_pin",
    )
    for y, visual_name in ((0.180, "trunnion_collar_0"), (-0.180, "trunnion_collar_1")):
        barrel.visual(
            Cylinder(radius=0.095, length=0.055),
            origin=Origin(xyz=(0.0, y, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=worn_steel,
            name=visual_name,
        )
    for y, visual_name in ((0.080, "recoil_tube_0"), (-0.080, "recoil_tube_1")):
        barrel.visual(
            Cylinder(radius=0.032, length=0.82),
            origin=Origin(xyz=(0.34, y, -0.060), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=worn_steel,
            name=visual_name,
        )
    barrel.visual(
        Cylinder(radius=0.052, length=0.025),
        origin=Origin(xyz=(1.158, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=bore_black,
        name="muzzle_bore",
    )

    for index, side in enumerate((1.0, -1.0)):
        trail = model.part(f"trail_{index}")
        trail.visual(
            Cylinder(radius=0.060, length=0.17),
            origin=Origin(),
            material=worn_steel,
            name="hinge_knuckle",
        )
        trail.visual(
            Box((0.16, 0.060, 0.070)),
            origin=Origin(xyz=(-0.08, 0.0, -0.010)),
            material=olive,
            name="trail_neck",
        )
        trail.visual(
            Box((1.22, 0.070, 0.080)),
            origin=Origin(xyz=(-0.74, 0.0, -0.025)),
            material=olive,
            name="trail_beam",
        )
        trail.visual(
            Box((0.20, 0.28, 0.18)),
            origin=Origin(xyz=(-1.38, 0.0, -0.135)),
            material=worn_steel,
            name="spade",
        )
        trail.visual(
            Box((0.24, 0.18, 0.040)),
            origin=Origin(xyz=(-1.32, 0.0, -0.235)),
            material=worn_steel,
            name="spade_foot",
        )
        model.articulation(
            f"carriage_to_trail_{index}",
            ArticulationType.REVOLUTE,
            parent=carriage,
            child=trail,
            origin=Origin(xyz=(TRAIL_HINGE_X, side * TRAIL_HINGE_Y, TRAIL_HINGE_Z)),
            axis=(0.0, 0.0, -side),
            motion_limits=MotionLimits(lower=0.0, upper=0.62, effort=90.0, velocity=0.7),
        )

    wheel_mesh = mesh_from_geometry(
        WheelGeometry(
            0.395,
            0.120,
            rim=WheelRim(inner_radius=0.305, flange_height=0.025, flange_thickness=0.010),
            hub=WheelHub(radius=0.075, width=0.145, cap_style="domed"),
            face=WheelFace(dish_depth=0.012, front_inset=0.004, rear_inset=0.004),
            spokes=WheelSpokes(style="straight", count=12, thickness=0.011, window_radius=0.022),
            bore=WheelBore(style="round", diameter=0.070),
        ),
        "artillery_spoked_wheel",
    )
    tire_mesh = mesh_from_geometry(
        TireGeometry(
            WHEEL_RADIUS,
            WHEEL_WIDTH,
            inner_radius=0.382,
            tread=TireTread(style="circumferential", depth=0.006, count=2),
            sidewall=TireSidewall(style="square", bulge=0.015),
            shoulder=TireShoulder(width=0.012, radius=0.004),
        ),
        "steel_road_tire",
    )
    for index, side in enumerate((1.0, -1.0)):
        wheel = model.part(f"wheel_{index}")
        wheel.visual(wheel_mesh, material=worn_steel, name="spoked_wheel")
        wheel.visual(tire_mesh, material=tire_steel, name="steel_tire")
        model.articulation(
            f"axle_to_wheel_{index}",
            ArticulationType.CONTINUOUS,
            parent=carriage,
            child=wheel,
            origin=Origin(xyz=(0.0, side * WHEEL_Y, AXLE_Z), rpy=(0.0, 0.0, math.pi / 2.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=60.0, velocity=18.0),
        )

    model.articulation(
        "carriage_to_barrel",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=barrel,
        origin=Origin(xyz=(TRUNNION_X, 0.0, TRUNNION_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.10, upper=0.72, effort=180.0, velocity=0.8),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
