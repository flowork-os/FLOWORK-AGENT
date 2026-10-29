# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, box_fan_with_control_knob, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: box_fan_with_control_knob

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

def rounded_rect_profile(width, height, radius, *, corner_segments=6):
    width = float(width); height = float(height); radius = float(radius)
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    corner_segments = max(1, int(corner_segments))
    max_r = 0.5 * min(width, height)
    if radius < 0 or radius > max_r:
        raise ValidationError("radius must be within [0, %s]" % max_r)
    hw = width * 0.5; hh = height * 0.5
    if radius <= 1e-12:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    r = radius

    def arc(cx, cy, a0, a1):
        out = []
        for i in range(corner_segments + 1):
            t = i / corner_segments
            a = a0 + (a1 - a0) * t
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return out

    pts = []
    pts.extend(arc(hw - r, -hh + r, -math.pi / 2.0, 0.0))
    pts.extend(arc(hw - r, hh - r, 0.0, math.pi / 2.0)[1:])
    pts.extend(arc(-hw + r, hh - r, math.pi / 2.0, math.pi)[1:])
    pts.extend(arc(-hw + r, -hh + r, math.pi, 3.0 * math.pi / 2.0)[1:])
    return pts

def _extrude_profile(points, height, *, center=True, z0=None):
    """Extrude a closed 2D profile (XY) by height along +Z. Returns cq.Solid."""
    pts = _ensure_ccw(_profile_points_2d(points))
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for (x, y) in pts], close=True))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, float(height)))
    dz = (-height / 2.0 if center else 0.0) if z0 is None else z0
    if dz:
        solid = solid.translate(cq.Vector(0, 0, dz))
    return solid

# ===== brackets_hinges_bezels (24 syms) =====
_EPS = 1e-9

def _dot(a, b):
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])

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

def _mat3_to_rpy(mat):
    pitch = math.asin(_brackets_hinges_bezels_clamp(-mat[2][0], -1.0, 1.0))
    cp = math.cos(pitch)
    if abs(cp) > 1e-8:
        roll = math.atan2(mat[2][1], mat[2][2])
        yaw = math.atan2(mat[1][0], mat[0][0])
        return (roll, pitch, yaw)
    roll = 0.0
    if pitch >= 0.0:
        yaw = math.atan2(-mat[0][1], mat[1][1])
    else:
        yaw = math.atan2(mat[0][1], mat[1][1])
    return (roll, pitch, yaw)

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

def _axis_vector(axis):
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

def _support_min_projection_on_element(geometry, tf, *, axis):
    center = (float(tf[0][3]), float(tf[1][3]), float(tf[2][3]))
    rot = _mat3_from_mat4(tf)
    axis_local = _mat3_vec3(_mat3_transpose(rot), axis)

    if isinstance(geometry, Sphere):
        return _dot(center, axis) - float(geometry.radius)
    if isinstance(geometry, Box):
        hx, hy, hz = (float(geometry.size[0]) * 0.5, float(geometry.size[1]) * 0.5,
                      float(geometry.size[2]) * 0.5)
        half = hx * abs(axis_local[0]) + hy * abs(axis_local[1]) + hz * abs(axis_local[2])
        return _dot(center, axis) - half
    if isinstance(geometry, Cylinder):
        radial = math.hypot(axis_local[0], axis_local[1])
        half = float(geometry.radius) * radial + (float(geometry.length) * 0.5) * abs(axis_local[2])
        return _dot(center, axis) - half
    # generic B-rep: support of its local AABB box (centered at AABB center)
    (mn, mx) = _geometry_local_aabb(geometry)
    c_local = ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5)
    hx, hy, hz = (mx[0] - mn[0]) * 0.5, (mx[1] - mn[1]) * 0.5, (mx[2] - mn[2]) * 0.5
    world_center = _mat4_vec3(tf, c_local)
    half = hx * abs(axis_local[0]) + hy * abs(axis_local[1]) + hz * abs(axis_local[2])
    return _dot(world_center, axis) - half

def _subject_min_projection(subject, *, axis, asset_root=None, prefer_collisions):
    projections = [
        _support_min_projection_on_element(geometry, tf, axis=axis)
        for geometry, tf in _iter_subject_items(subject, prefer_collisions=prefer_collisions)
    ]
    if not projections:
        raise ValidationError("child has no geometry to compute support distance")
    return min(projections)

def place_on_surface(
    child,
    target,
    *,
    point_hint=None,
    direction=None,
    child_axis="+z",
    clearance=0.0,
    spin=0.0,
    asset_root=None,
    prefer_collisions=False,
    child_prefer_collisions=False,
    up_hint=(0.0, 0.0, 1.0),
):
    """Rigidly place a child on a target surface using a tangent-frame mount."""
    frame = surface_frame(
        target, point_hint=point_hint, direction=direction,
        prefer_collisions=prefer_collisions, up_hint=up_hint,
    )
    child_axis_vec = _axis_vector(child_axis)
    mount_proj = _subject_min_projection(
        child, axis=child_axis_vec, prefer_collisions=child_prefer_collisions
    )
    offset = float(clearance) - float(mount_proj)
    xyz = (
        frame.point[0] + frame.normal[0] * offset,
        frame.point[1] + frame.normal[1] * offset,
        frame.point[2] + frame.normal[2] * offset,
    )
    rot = _rotation_for_surface_frame(frame, child_axis=child_axis, spin=float(spin))
    return Origin(xyz=xyz, rpy=_mat3_to_rpy(rot))

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

# ===== sweeps (11 syms) =====
def _v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

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

# ===== model =====
import math
def _rounded_rect_mesh(
    name: str,
    *,
    width: float,
    depth: float,
    height: float,
    radius: float,
):
    return mesh_from_geometry(
        ExtrudeGeometry.from_z0(
            rounded_rect_profile(width, depth, radius, corner_segments=10),
            height,
            cap=True,
            closed=True,
        ),
        name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_fan")

    body = model.material("body", rgba=(0.82, 0.84, 0.86, 1.0))
    charcoal = model.material("charcoal", rgba=(0.20, 0.22, 0.24, 1.0))
    black = model.material("black", rgba=(0.08, 0.09, 0.10, 1.0))
    dark_grey = model.material("dark_grey", rgba=(0.31, 0.33, 0.35, 1.0))
    steel = model.material("steel", rgba=(0.61, 0.65, 0.69, 1.0))

    base_width = 0.34
    base_depth = 0.24
    base_height = 0.045

    housing_width = 0.13
    housing_depth = 0.11
    wall_thickness = 0.004
    collar_radius = 0.07
    collar_height = 0.018
    column_bottom = 0.014
    column_height = 0.908
    column_top = column_bottom + column_height
    top_cap_height = 0.014

    front_opening_width = 0.064
    front_opening_bottom = 0.118
    front_opening_height = 0.722
    front_opening_top = front_opening_bottom + front_opening_height

    rear_opening_width = 0.084
    rear_opening_bottom = 0.148
    rear_opening_height = 0.582
    rear_opening_top = rear_opening_bottom + rear_opening_height

    impeller_radius = 0.041
    impeller_height = 0.742
    impeller_center_y = 0.008
    impeller_center_z = 0.462

    base = model.part("pedestal_base")
    base.visual(
        _rounded_rect_mesh(
            "tower_fan_base_shell",
            width=base_width,
            depth=base_depth,
            height=base_height,
            radius=0.060,
        ),
        material=charcoal,
        name="base_shell",
    )
    base.visual(
        Cylinder(radius=0.074, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, base_height - 0.004)),
        material=dark_grey,
        name="bearing_pad",
    )

    housing = model.part("tower_housing")
    housing.visual(
        Cylinder(radius=collar_radius, length=collar_height),
        origin=Origin(xyz=(0.0, 0.0, collar_height * 0.5)),
        material=body,
        name="turntable_collar",
    )
    housing.visual(
        Cylinder(radius=0.026, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, 0.011)),
        material=dark_grey,
        name="drive_hub",
    )
    side_panel_height = column_height
    side_panel_z = column_bottom + (side_panel_height * 0.5)
    side_x = (housing_width - wall_thickness) * 0.5
    housing.visual(
        Box((wall_thickness, housing_depth, side_panel_height)),
        origin=Origin(xyz=(-side_x, 0.0, side_panel_z)),
        material=body,
        name="left_side_panel",
    )
    housing.visual(
        Box((wall_thickness, housing_depth, side_panel_height)),
        origin=Origin(xyz=(side_x, 0.0, side_panel_z)),
        material=body,
        name="right_side_panel",
    )

    front_face_y = (housing_depth - wall_thickness) * 0.5
    front_upper_height = column_top - front_opening_top
    front_lower_height = front_opening_bottom - column_bottom
    front_stile_width = 0.019
    front_stile_x = (front_opening_width * 0.5) + (front_stile_width * 0.5) - 0.001
    housing.visual(
        Box((housing_width - (2.0 * wall_thickness), wall_thickness, front_lower_height)),
        origin=Origin(
            xyz=(
                0.0,
                front_face_y,
                column_bottom + (front_lower_height * 0.5),
            )
        ),
        material=body,
        name="front_lower_panel",
    )
    housing.visual(
        Box((housing_width - (2.0 * wall_thickness), wall_thickness, front_upper_height)),
        origin=Origin(
            xyz=(
                0.0,
                front_face_y,
                front_opening_top + (front_upper_height * 0.5),
            )
        ),
        material=body,
        name="front_upper_panel",
    )
    housing.visual(
        Box((front_stile_width, wall_thickness, front_opening_height + 0.004)),
        origin=Origin(
            xyz=(
                -front_stile_x,
                front_face_y,
                front_opening_bottom + (front_opening_height * 0.5),
            )
        ),
        material=body,
        name="front_left_stile",
    )
    housing.visual(
        Box((front_stile_width, wall_thickness, front_opening_height + 0.004)),
        origin=Origin(
            xyz=(
                front_stile_x,
                front_face_y,
                front_opening_bottom + (front_opening_height * 0.5),
            )
        ),
        material=body,
        name="front_right_stile",
    )
    for index in range(11):
        z = front_opening_bottom + 0.040 + (index * 0.060)
        housing.visual(
            Box((front_opening_width + 0.004, wall_thickness * 0.8, 0.005)),
            origin=Origin(xyz=(0.0, front_face_y - 0.0008, z)),
            material=black,
            name=f"front_grille_slat_{index:02d}",
        )

    rear_face_y = -front_face_y
    rear_lower_height = rear_opening_bottom - column_bottom
    rear_upper_height = column_top - rear_opening_top
    rear_stile_width = 0.016
    rear_stile_x = (rear_opening_width * 0.5) + (rear_stile_width * 0.5) - 0.001
    housing.visual(
        Box((housing_width - (2.0 * wall_thickness), wall_thickness, rear_lower_height)),
        origin=Origin(
            xyz=(
                0.0,
                rear_face_y,
                column_bottom + (rear_lower_height * 0.5),
            )
        ),
        material=body,
        name="rear_lower_panel",
    )
    housing.visual(
        Box((housing_width - (2.0 * wall_thickness), wall_thickness, rear_upper_height)),
        origin=Origin(
            xyz=(
                0.0,
                rear_face_y,
                rear_opening_top + (rear_upper_height * 0.5),
            )
        ),
        material=body,
        name="rear_top_panel",
    )
    housing.visual(
        Box((rear_stile_width, wall_thickness, rear_opening_height + 0.004)),
        origin=Origin(
            xyz=(
                -rear_stile_x,
                rear_face_y,
                rear_opening_bottom + (rear_opening_height * 0.5),
            )
        ),
        material=body,
        name="rear_left_stile",
    )
    housing.visual(
        Box((rear_stile_width, wall_thickness, rear_opening_height + 0.004)),
        origin=Origin(
            xyz=(
                rear_stile_x,
                rear_face_y,
                rear_opening_bottom + (rear_opening_height * 0.5),
            )
        ),
        material=body,
        name="rear_right_stile",
    )
    rear_slat_span = rear_opening_width - 0.010
    for index in range(12):
        if index == 5:
            x = -0.004
        elif index == 6:
            x = 0.004
        else:
            x = -rear_slat_span * 0.5 + (rear_slat_span * index / 11.0)
        housing.visual(
            Box((0.003, wall_thickness, rear_opening_height + 0.004)),
            origin=Origin(
                xyz=(
                    x,
                    rear_face_y,
                    rear_opening_bottom + (rear_opening_height * 0.5),
                )
            ),
            material=black,
            name=f"rear_intake_slat_{index:02d}",
        )

    housing.visual(
        Box((0.040, housing_depth - (2.0 * wall_thickness), 0.024)),
        origin=Origin(xyz=(0.0, 0.0, 0.069)),
        material=dark_grey,
        name="lower_motor_cradle",
    )
    housing.visual(
        Cylinder(radius=0.013, length=0.010),
        origin=Origin(
            xyz=(
                0.0,
                impeller_center_y,
                impeller_center_z - (impeller_height * 0.5) - 0.005,
            )
        ),
        material=dark_grey,
        name="lower_bearing_boss",
    )
    housing.visual(
        Box((housing_width - (2.0 * wall_thickness), 0.020, 0.012)),
        origin=Origin(xyz=(0.0, impeller_center_y, 0.849)),
        material=dark_grey,
        name="upper_bearing_bridge",
    )
    housing.visual(
        Cylinder(radius=0.013, length=0.010),
        origin=Origin(
            xyz=(
                0.0,
                impeller_center_y,
                impeller_center_z + (impeller_height * 0.5) + 0.005,
            )
        ),
        material=dark_grey,
        name="upper_bearing_boss",
    )

    housing.visual(
        _rounded_rect_mesh(
            "tower_fan_top_cap",
            width=housing_width - 0.006,
            depth=housing_depth - 0.006,
            height=top_cap_height,
            radius=0.028,
        ),
        origin=Origin(xyz=(0.0, 0.0, column_top - top_cap_height)),
        material=body,
        name="top_cap",
    )
    housing.visual(
        Box((0.020, 0.010, 0.004)),
        origin=Origin(xyz=(0.0, rear_face_y - 0.001, column_top - 0.040)),
        material=dark_grey,
        name="rear_switch_panel",
    )

    impeller = model.part("impeller_drum")
    impeller.visual(
        Cylinder(radius=0.008, length=impeller_height),
        material=dark_grey,
        name="axle",
    )
    impeller.visual(
        Cylinder(radius=impeller_radius, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, -(impeller_height * 0.5) + 0.007)),
        material=steel,
        name="lower_end_disc",
    )
    impeller.visual(
        Cylinder(radius=impeller_radius, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, (impeller_height * 0.5) - 0.007)),
        material=steel,
        name="upper_end_disc",
    )
    blade_radius = 0.031
    for index in range(16):
        angle = (2.0 * math.pi * index) / 16.0
        impeller.visual(
            Box((0.004, 0.016, impeller_height + 0.004)),
            origin=Origin(
                xyz=(
                    blade_radius * math.cos(angle),
                    blade_radius * math.sin(angle),
                    0.0,
                ),
                rpy=(0.0, 0.0, angle + 0.32),
            ),
            material=steel,
            name=f"blade_{index:02d}",
        )

    knob = model.part("speed_selector_knob")
    knob.visual(
        Cylinder(radius=0.018, length=0.022),
        origin=Origin(xyz=(0.0, -0.011, 0.0), rpy=(math.pi * 0.5, 0.0, 0.0)),
        material=charcoal,
        name="knob_body",
    )
    knob.visual(
        Box((0.003, 0.004, 0.010)),
        origin=Origin(xyz=(0.0, -0.020, 0.012)),
        material=steel,
        name="indicator_ridge",
    )

    model.articulation(
        "base_oscillation",
        ArticulationType.REVOLUTE,
        parent=base,
        child=housing,
        origin=Origin(xyz=(0.0, 0.0, base_height)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.0,
            lower=-1.05,
            upper=1.05,
        ),
    )
    model.articulation(
        "housing_to_impeller",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=impeller,
        origin=Origin(xyz=(0.0, impeller_center_y, impeller_center_z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=2.0,
            velocity=18.0,
        ),
    )
    model.articulation(
        "housing_to_speed_knob",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=knob,
        origin=place_on_surface(
            knob,
            housing.get_visual("rear_top_panel"),
            point_hint=(0.0, -housing_depth * 0.5, 0.782),
            child_axis="-y",
            clearance=0.0,
        ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.25,
            velocity=2.5,
            lower=0.0,
            upper=4.8,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
