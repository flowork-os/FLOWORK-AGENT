# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

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

# ===== model =====
import math
def _circle_profile(
    radius: float, *, segments: int = 72, start_angle: float = 0.0
) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos(start_angle + (2.0 * math.pi * index / segments)),
            radius * math.sin(start_angle + (2.0 * math.pi * index / segments)),
        )
        for index in range(segments)
    ]
def _ring_mesh(
    *,
    name: str,
    outer_radius: float,
    inner_radius: float,
    thickness: float,
    through_holes: list[tuple[float, float, float]] | None = None,
) -> object:
    hole_profiles = [_circle_profile(inner_radius, segments=56)]
    for cx, cy, radius in through_holes or []:
        hole_profiles.append(
            [(cx + x, cy + y) for x, y in _circle_profile(radius, segments=28)]
        )
    ring_geom = ExtrudeWithHolesGeometry(
        _circle_profile(outer_radius, segments=96),
        hole_profiles,
        height=thickness,
        center=True,
    ).rotate_x(math.pi / 2.0)
    return mesh_from_geometry(ring_geom, name)
def _crank_arm_mesh(name: str, *, thickness: float = 0.016) -> object:
    outline = [
        (0.020, 0.018),
        (0.018, 0.002),
        (0.015, -0.030),
        (0.012, -0.078),
        (0.011, -0.126),
        (0.013, -0.160),
        (0.010, -0.176),
        (0.006, -0.184),
        (-0.006, -0.184),
        (-0.010, -0.176),
        (-0.013, -0.160),
        (-0.011, -0.126),
        (-0.012, -0.078),
        (-0.015, -0.030),
        (-0.018, 0.002),
        (-0.020, 0.018),
        (-0.012, 0.026),
        (0.012, 0.026),
    ]
    arm_geom = ExtrudeGeometry.centered(outline, thickness).rotate_x(math.pi / 2.0)
    return mesh_from_geometry(arm_geom, name)
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
def _add_member(part, a, b, radius: float, material, *, name: str | None = None) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_cylinder(a, b)),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="fixie_crankset")

    alloy = model.material("alloy", rgba=(0.78, 0.80, 0.83, 1.0))
    brushed_steel = model.material("brushed_steel", rgba=(0.63, 0.65, 0.68, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.23, 0.24, 0.27, 1.0))
    matte_black = model.material("matte_black", rgba=(0.08, 0.08, 0.09, 1.0))
    pedal_black = model.material("pedal_black", rgba=(0.15, 0.15, 0.16, 1.0))
    reflector_amber = model.material("reflector_amber", rgba=(0.82, 0.46, 0.10, 1.0))

    shell_length = 0.0865
    shell_half = shell_length * 0.5
    shell_outer_radius = 0.024
    shell_end_bore_radius = 0.016
    shell_mid_bore_radius = 0.019

    shell_outer_profile = [
        (0.023, -shell_half),
        (shell_outer_radius, -shell_half + 0.003),
        (shell_outer_radius, shell_half - 0.003),
        (0.023, shell_half),
    ]
    shell_inner_profile = [
        (shell_end_bore_radius, -shell_half),
        (shell_end_bore_radius, -shell_half + 0.010),
        (shell_mid_bore_radius, -0.020),
        (shell_mid_bore_radius, 0.020),
        (shell_end_bore_radius, shell_half - 0.010),
        (shell_end_bore_radius, shell_half),
    ]
    shell_mesh = mesh_from_geometry(
        LatheGeometry.from_shell_profiles(
            shell_outer_profile,
            shell_inner_profile,
            segments=88,
            start_cap="flat",
            end_cap="flat",
        ).rotate_x(math.pi / 2.0),
        "bb_shell",
    )

    crank_arm_mesh = _crank_arm_mesh("forged_crank_arm")
    chainring_mesh = _ring_mesh(
        name="track_chainring",
        outer_radius=0.094,
        inner_radius=0.038,
        thickness=0.004,
        through_holes=[
            (
                0.048 * math.cos((2.0 * math.pi * index) / 5.0),
                0.048 * math.sin((2.0 * math.pi * index) / 5.0),
                0.0045,
            )
            for index in range(5)
        ]
        + [
            (
                0.067 * math.cos((2.0 * math.pi * index) / 5.0 + math.pi / 5.0),
                0.067 * math.sin((2.0 * math.pi * index) / 5.0 + math.pi / 5.0),
                0.010,
            )
            for index in range(5)
        ],
    )

    bb_shell = model.part("bb_shell")
    bb_shell.visual(shell_mesh, material=matte_black, name="shell_body")
    bb_shell.visual(
        Cylinder(radius=0.0215, length=0.004),
        origin=Origin(xyz=(0.0, shell_half + 0.002, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="drive_side_dust_cover",
    )
    bb_shell.visual(
        Cylinder(radius=0.0215, length=0.004),
        origin=Origin(xyz=(0.0, -shell_half - 0.002, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="non_drive_side_dust_cover",
    )
    bb_shell.inertial = Inertial.from_geometry(
        Cylinder(radius=shell_outer_radius, length=shell_length),
        mass=0.30,
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
    )

    spindle = model.part("spindle")
    spindle.visual(
        Cylinder(radius=0.012, length=shell_length),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=brushed_steel,
        name="spindle_axle",
    )
    spindle.visual(
        Cylinder(radius=0.021, length=0.003),
        origin=Origin(xyz=(0.0, shell_half + 0.0015, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="drive_side_collar",
    )
    spindle.visual(
        Cylinder(radius=0.021, length=0.003),
        origin=Origin(xyz=(0.0, -shell_half - 0.0015, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="non_drive_side_collar",
    )
    spindle.inertial = Inertial.from_geometry(
        Cylinder(radius=0.021, length=shell_length),
        mass=0.45,
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
    )

    right_crank = model.part("right_crank")
    right_crank.visual(
        Cylinder(radius=0.018, length=0.016),
        origin=Origin(xyz=(0.0, 0.008, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=alloy,
        name="spindle_boss",
    )
    right_crank.visual(
        crank_arm_mesh,
        origin=Origin(xyz=(0.0, 0.014, 0.0)),
        material=alloy,
        name="arm_blade",
    )
    right_crank.visual(
        Cylinder(radius=0.022, length=0.010),
        origin=Origin(xyz=(0.0, 0.014, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=alloy,
        name="spider_carrier",
    )
    spider_root = (0.0, 0.014, 0.0)
    for index in range(5):
        angle = (2.0 * math.pi * index) / 5.0
        bolt_center = (0.048 * math.cos(angle), 0.014, 0.048 * math.sin(angle))
        _add_member(
            right_crank,
            spider_root,
            bolt_center,
            0.004,
            alloy,
            name=f"spider_arm_{index}",
        )
        right_crank.visual(
            Cylinder(radius=0.0085, length=0.004),
            origin=Origin(
                xyz=(bolt_center[0], 0.012, bolt_center[2]),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=alloy,
            name=f"bolt_pad_{index}",
        )
    right_crank.visual(
        Cylinder(radius=0.0105, length=0.020),
        origin=Origin(xyz=(0.0, 0.018, -0.170), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=alloy,
        name="pedal_eye",
    )
    right_crank.visual(
        Cylinder(radius=0.0045, length=0.014),
        origin=Origin(xyz=(0.0, 0.035, -0.170), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=brushed_steel,
        name="pedal_stub",
    )
    right_crank.inertial = Inertial.from_geometry(
        Box((0.040, 0.035, 0.210)),
        mass=0.42,
        origin=Origin(xyz=(0.0, 0.010, -0.085)),
    )

    left_crank = model.part("left_crank")
    left_crank.visual(
        Cylinder(radius=0.018, length=0.016),
        origin=Origin(xyz=(0.0, -0.008, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=alloy,
        name="spindle_boss",
    )
    left_crank.visual(
        crank_arm_mesh,
        origin=Origin(xyz=(0.0, -0.014, 0.0), rpy=(math.pi, 0.0, 0.0)),
        material=alloy,
        name="arm_blade",
    )
    left_crank.visual(
        Cylinder(radius=0.0105, length=0.020),
        origin=Origin(xyz=(0.0, -0.018, 0.170), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=alloy,
        name="pedal_eye",
    )
    left_crank.visual(
        Cylinder(radius=0.0045, length=0.014),
        origin=Origin(xyz=(0.0, -0.035, 0.170), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=brushed_steel,
        name="pedal_stub",
    )
    left_crank.inertial = Inertial.from_geometry(
        Box((0.040, 0.035, 0.210)),
        mass=0.40,
        origin=Origin(xyz=(0.0, -0.010, 0.085)),
    )

    chainring = model.part("chainring")
    chainring.visual(
        chainring_mesh,
        origin=Origin(xyz=(0.0, 0.020, 0.0)),
        material=dark_steel,
        name="ring_plate",
    )
    for index in range(5):
        angle = (2.0 * math.pi * index) / 5.0
        bx = 0.048 * math.cos(angle)
        bz = 0.048 * math.sin(angle)
        chainring.visual(
            Cylinder(radius=0.006, length=0.004),
            origin=Origin(
                xyz=(bx, 0.016, bz),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=brushed_steel,
            name=f"bolt_{index}",
        )
    chainring.inertial = Inertial.from_geometry(
        Cylinder(radius=0.094, length=0.004),
        mass=0.19,
        origin=Origin(xyz=(0.0, 0.020, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
    )

    right_pedal = model.part("right_pedal")
    right_pedal.visual(
        Cylinder(radius=0.008, length=0.016),
        origin=Origin(xyz=(0.0, 0.022, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=brushed_steel,
        name="pedal_sleeve",
    )
    right_pedal.visual(
        Box((0.090, 0.050, 0.014)),
        origin=Origin(xyz=(0.0, 0.045, 0.0)),
        material=pedal_black,
        name="platform_body",
    )
    right_pedal.visual(
        Box((0.012, 0.050, 0.018)),
        origin=Origin(xyz=(0.036, 0.045, 0.0)),
        material=pedal_black,
        name="front_cage",
    )
    right_pedal.visual(
        Box((0.012, 0.050, 0.018)),
        origin=Origin(xyz=(-0.036, 0.045, 0.0)),
        material=pedal_black,
        name="rear_cage",
    )
    right_pedal.visual(
        Box((0.012, 0.004, 0.016)),
        origin=Origin(xyz=(0.030, 0.063, 0.014)),
        material=reflector_amber,
        name="pedal_reflector",
    )
    right_pedal.inertial = Inertial.from_geometry(
        Box((0.090, 0.070, 0.024)),
        mass=0.12,
        origin=Origin(xyz=(0.0, 0.045, 0.0)),
    )

    left_pedal = model.part("left_pedal")
    left_pedal.visual(
        Cylinder(radius=0.008, length=0.016),
        origin=Origin(xyz=(0.0, -0.022, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=brushed_steel,
        name="pedal_sleeve",
    )
    left_pedal.visual(
        Box((0.090, 0.050, 0.014)),
        origin=Origin(xyz=(0.0, -0.045, 0.0)),
        material=pedal_black,
        name="platform_body",
    )
    left_pedal.visual(
        Box((0.012, 0.050, 0.018)),
        origin=Origin(xyz=(0.036, -0.045, 0.0)),
        material=pedal_black,
        name="front_cage",
    )
    left_pedal.visual(
        Box((0.012, 0.050, 0.018)),
        origin=Origin(xyz=(-0.036, -0.045, 0.0)),
        material=pedal_black,
        name="rear_cage",
    )
    left_pedal.visual(
        Box((0.012, 0.004, 0.016)),
        origin=Origin(xyz=(0.030, -0.063, 0.014)),
        material=reflector_amber,
        name="pedal_reflector",
    )
    left_pedal.inertial = Inertial.from_geometry(
        Box((0.090, 0.070, 0.024)),
        mass=0.12,
        origin=Origin(xyz=(0.0, -0.045, 0.0)),
    )

    model.articulation(
        "shell_to_spindle",
        ArticulationType.CONTINUOUS,
        parent=bb_shell,
        child=spindle,
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=60.0, velocity=18.0),
    )
    model.articulation(
        "spindle_to_right_crank",
        ArticulationType.FIXED,
        parent=spindle,
        child=right_crank,
        origin=Origin(xyz=(0.0, shell_half + 0.003, 0.0)),
    )
    model.articulation(
        "spindle_to_left_crank",
        ArticulationType.FIXED,
        parent=spindle,
        child=left_crank,
        origin=Origin(xyz=(0.0, -shell_half - 0.003, 0.0)),
    )
    model.articulation(
        "right_crank_to_chainring",
        ArticulationType.FIXED,
        parent=right_crank,
        child=chainring,
        origin=Origin(),
    )
    model.articulation(
        "right_crank_to_pedal",
        ArticulationType.CONTINUOUS,
        parent=right_crank,
        child=right_pedal,
        origin=Origin(xyz=(0.0, 0.028, -0.170)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=28.0),
    )
    model.articulation(
        "left_crank_to_pedal",
        ArticulationType.CONTINUOUS,
        parent=left_crank,
        child=left_pedal,
        origin=Origin(xyz=(0.0, -0.028, 0.170)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=28.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
