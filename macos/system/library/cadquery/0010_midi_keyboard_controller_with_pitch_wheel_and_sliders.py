# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, midi_keyboard_controller_with_pitch_wheel_and_sliders, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: midi_keyboard_controller_with_pitch_wheel_and_sliders

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

def _profile_points_3d(profile):
    points = [(float(x), float(y), float(z)) for (x, y, z) in profile]
    cleaned = []
    for pt in points:
        if not cleaned or not (abs(cleaned[-1][0] - pt[0]) <= 1e-9 and abs(cleaned[-1][1] - pt[1]) <= 1e-9 and abs(cleaned[-1][2] - pt[2]) <= 1e-9):
            cleaned.append(pt)
    if len(cleaned) >= 2 and abs(cleaned[0][0] - cleaned[-1][0]) <= 1e-9 and abs(cleaned[0][1] - cleaned[-1][1]) <= 1e-9 and abs(cleaned[0][2] - cleaned[-1][2]) <= 1e-9:
        cleaned = cleaned[:-1]
    if len(cleaned) < 2:
        raise ValidationError("Profile must have at least 2 unique points")
    return cleaned

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

# ===== lathe_extrude_loft (4 syms) =====
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

def _xy_area(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return a * 0.5

def _loft_solid(rings, *, cap, closed, ruled=True):
    """Loft through a list of 3D rings. cap+closed -> solid via makeLoft;
    otherwise an open side-wall shell. Rings are oriented consistently first."""
    rings = [list(r) for r in rings]
    if len(rings) < 2:
        raise ValidationError("Loft requires at least two profiles")
    base = _xy_area(rings[0])
    if abs(base) > 1e-9:
        if base < 0:
            rings = [list(reversed(r)) for r in rings]
            base = -base
        for idx in range(len(rings)):
            if _xy_area(rings[idx]) * base < 0:
                rings[idx] = list(reversed(rings[idx]))
    if cap and closed:
        wires = [cq.Wire.makePolygon([cq.Vector(*p) for p in r], close=True) for r in rings]
        return cq.Solid.makeLoft(wires, ruled)
    faces = _loft_side_faces(rings, closed)
    if not faces:
        raise ValidationError("Loft produced no valid side faces")
    return cq.Shell.makeShell(faces)

class LoftGeometry(MeshGeometry):
    """Loft through a sequence of closed 3D profiles (each a list of (x,y,z))."""

    def __init__(self, profiles, *, cap=True, closed=True):
        super().__init__()
        profile_list = [_profile_points_3d(p) for p in profiles]
        if len(profile_list) < 2:
            raise ValidationError("Loft requires at least two profiles")

        ring_count = len(profile_list[0])
        if closed and ring_count < 3:
            raise ValidationError("Closed loft profiles must have at least 3 points")
        for profile in profile_list:
            if len(profile) != ring_count:
                raise ValidationError("Loft profiles must have the same point count")

        self._set(_loft_solid(profile_list, cap=cap, closed=closed))

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
ASSETS = AssetContext.from_script(__file__)
def _add_quad(geom: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    geom.add_face(a, b, c)
    geom.add_face(a, c, d)
def _build_rear_housing_mesh() -> MeshGeometry:
    geom = MeshGeometry()

    vertices = [
        (-0.250, 0.000, 0.000),
        (0.250, 0.000, 0.000),
        (0.250, 0.095, 0.000),
        (-0.250, 0.095, 0.000),
        (-0.246, 0.000, 0.028),
        (0.246, 0.000, 0.028),
        (0.248, 0.095, 0.044),
        (-0.248, 0.095, 0.044),
    ]
    ids = [geom.add_vertex(*vertex) for vertex in vertices]

    _add_quad(geom, ids[0], ids[1], ids[2], ids[3])  # bottom
    _add_quad(geom, ids[4], ids[7], ids[6], ids[5])  # top
    _add_quad(geom, ids[0], ids[4], ids[5], ids[1])  # front
    _add_quad(geom, ids[1], ids[5], ids[6], ids[2])  # right
    _add_quad(geom, ids[2], ids[6], ids[7], ids[3])  # back
    _add_quad(geom, ids[3], ids[7], ids[4], ids[0])  # left
    return geom
def _arc_points_2d(
    cx: float,
    cy: float,
    radius: float,
    start_angle: float,
    end_angle: float,
    *,
    segments: int,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(segments + 1):
        t = index / segments
        angle = start_angle + (end_angle - start_angle) * t
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points
def _build_white_key_outline(
    *,
    width: float,
    depth: float,
    rear_width: float,
    shoulder_y: float,
    left_relief: bool,
    right_relief: bool,
) -> list[tuple[float, float]]:
    half_width = width * 0.5
    rear_half_width = min(half_width - 0.0008, rear_width * 0.5)
    front_y = -depth * 0.5
    rear_y = depth * 0.5
    shoulder_y = min(rear_y - 0.004, max(front_y + 0.006, shoulder_y))
    front_radius = min(0.0025, half_width * 0.45, depth * 0.12)

    right_rear_x = rear_half_width if right_relief else half_width
    left_rear_x = -rear_half_width if left_relief else -half_width

    outline: list[tuple[float, float]] = [(right_rear_x, rear_y)]
    if right_relief:
        outline.append((right_rear_x, shoulder_y))
        outline.append((half_width, shoulder_y))
    outline.append((half_width, front_y + front_radius))
    outline.extend(
        _arc_points_2d(
            half_width - front_radius,
            front_y + front_radius,
            front_radius,
            0.0,
            -math.pi / 2.0,
            segments=4,
        )[1:]
    )
    outline.append((-half_width + front_radius, front_y))
    outline.extend(
        _arc_points_2d(
            -half_width + front_radius,
            front_y + front_radius,
            front_radius,
            -math.pi / 2.0,
            -math.pi,
            segments=4,
        )[1:]
    )
    outline.append((-half_width, shoulder_y))
    if left_relief:
        outline.append((left_rear_x, shoulder_y))
        outline.append((left_rear_x, rear_y))
    else:
        outline.append((-half_width, rear_y))
    return outline
def _write_white_key_mesh(
    mesh_name: str,
    *,
    width: float,
    depth: float,
    height: float,
    rear_width: float,
    shoulder_y: float,
    left_relief: bool,
    right_relief: bool,
):
    lower_outline = _build_white_key_outline(
        width=width,
        depth=depth,
        rear_width=rear_width,
        shoulder_y=shoulder_y,
        left_relief=left_relief,
        right_relief=right_relief,
    )
    upper_outline = _build_white_key_outline(
        width=width - 0.0018,
        depth=depth - 0.0016,
        rear_width=max(rear_width - 0.0020, 0.0080),
        shoulder_y=shoulder_y + 0.0006,
        left_relief=left_relief,
        right_relief=right_relief,
    )
    geom = LoftGeometry(
        [
            [(x, y, 0.0) for x, y in lower_outline],
            [(x, y, height) for x, y in upper_outline],
        ],
        cap=True,
        closed=True,
    )
    return mesh_from_geometry(geom, ASSETS.mesh_path(mesh_name))
def _build_black_key_outline(
    *,
    width: float,
    front_depth: float,
    rear_depth: float,
    front_radius: float,
) -> list[tuple[float, float]]:
    half_width = width * 0.5
    rear_y = rear_depth
    front_y = -front_depth
    front_radius = min(front_radius, half_width * 0.45, front_depth * 0.35)

    outline: list[tuple[float, float]] = [(half_width, rear_y)]
    outline.append((half_width, front_y + front_radius))
    outline.extend(
        _arc_points_2d(
            half_width - front_radius,
            front_y + front_radius,
            front_radius,
            0.0,
            -math.pi / 2.0,
            segments=4,
        )[1:]
    )
    outline.append((-half_width + front_radius, front_y))
    outline.extend(
        _arc_points_2d(
            -half_width + front_radius,
            front_y + front_radius,
            front_radius,
            -math.pi / 2.0,
            -math.pi,
            segments=4,
        )[1:]
    )
    outline.append((-half_width, rear_y))
    return outline
def _write_black_key_mesh(mesh_name: str):
    lower_profile = _build_black_key_outline(
        width=0.0132,
        front_depth=0.042,
        rear_depth=0.005,
        front_radius=0.0024,
    )
    shoulder_profile = _build_black_key_outline(
        width=0.0128,
        front_depth=0.036,
        rear_depth=0.004,
        front_radius=0.0022,
    )
    upper_profile = _build_black_key_outline(
        width=0.0104,
        front_depth=0.026,
        rear_depth=0.003,
        front_radius=0.0019,
    )
    geom = LoftGeometry(
        [
            [(x, y, 0.0) for x, y in lower_profile],
            [(x, y - 0.001, 0.006) for x, y in shoulder_profile],
            [(x, y - 0.003, 0.012) for x, y in upper_profile],
        ],
        cap=True,
        closed=True,
    )
    return mesh_from_geometry(geom, ASSETS.mesh_path(mesh_name))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="midi_keyboard", assets=ASSETS)

    body = model.material("body_charcoal", rgba=(0.17, 0.18, 0.20, 1.0))
    deck = model.material("deck_black", rgba=(0.10, 0.11, 0.12, 1.0))
    key_white = model.material("key_white", rgba=(0.94, 0.95, 0.96, 1.0))
    key_black = model.material("key_black", rgba=(0.08, 0.08, 0.09, 1.0))
    knob_dark = model.material("knob_dark", rgba=(0.14, 0.15, 0.16, 1.0))
    pad_rubber = model.material("pad_rubber", rgba=(0.22, 0.23, 0.25, 1.0))
    wheel_rubber = model.material("wheel_rubber", rgba=(0.12, 0.12, 0.13, 1.0))
    display_glass = model.material("display_glass", rgba=(0.18, 0.29, 0.34, 0.45))
    accent = model.material("accent_grey", rgba=(0.44, 0.46, 0.49, 1.0))

    chassis = model.part("chassis")
    rear_housing_mesh = mesh_from_geometry(
        _build_rear_housing_mesh(),
        ASSETS.mesh_path("midi_keyboard_rear_housing.obj"),
    )
    rear_housing = chassis.visual(rear_housing_mesh, material=body, name="rear_housing")
    chassis.visual(
        Box((0.500, 0.100, 0.018)),
        origin=Origin(xyz=(0.000, -0.050, 0.009)),
        material=body,
        name="front_base",
    )
    chassis.visual(
        Box((0.382, 0.010, 0.020)),
        origin=Origin(xyz=(0.000, 0.030, 0.010)),
        material=deck,
        name="rear_key_wall",
    )
    chassis.visual(
        Box((0.010, 0.115, 0.024)),
        origin=Origin(xyz=(-0.186, -0.026, 0.012)),
        material=deck,
        name="left_key_cheek",
    )
    chassis.visual(
        Box((0.010, 0.115, 0.024)),
        origin=Origin(xyz=(0.186, -0.026, 0.012)),
        material=deck,
        name="right_key_cheek",
    )
    chassis.visual(
        Box((0.358, 0.114, 0.002)),
        origin=Origin(xyz=(0.000, -0.026, 0.017)),
        material=deck,
        name="keybed_seat",
    )
    chassis.visual(
        Box((0.322, 0.034, 0.002)),
        origin=Origin(xyz=(0.000, -0.004, 0.023)),
        material=deck,
        name="black_key_seat",
    )
    chassis.visual(
        Box((0.496, 0.008, 0.006)),
        origin=Origin(xyz=(0.000, -0.094, 0.015)),
        material=accent,
        name="front_trim",
    )
    chassis.visual(
        Box((0.358, 0.114, 0.002)),
        origin=Origin(xyz=(0.000, -0.026, 0.019)),
        material=deck,
        name="white_key_support",
    )
    chassis.inertial = Inertial.from_geometry(
        Box((0.500, 0.195, 0.055)),
        mass=2.8,
        origin=Origin(xyz=(0.000, 0.000, 0.0275)),
    )

    white_key_width = 0.0222
    white_key_pitch = 0.0235
    white_key_centers = [(-7 + index) * white_key_pitch for index in range(15)]
    black_key_positions = {0, 1, 3, 4, 5, 7, 8, 10, 11, 12}
    white_key_mesh_cache: dict[tuple[bool, bool], object] = {}
    for index, center_x in enumerate(white_key_centers):
        left_relief = (index - 1) in black_key_positions
        right_relief = index in black_key_positions
        cache_key = (left_relief, right_relief)
        white_key_mesh = white_key_mesh_cache.get(cache_key)
        if white_key_mesh is None:
            variant_name = f"white_key_{int(left_relief)}{int(right_relief)}.obj"
            white_key_mesh = _write_white_key_mesh(
                variant_name,
                width=white_key_width * 0.92,
                depth=0.080,
                height=0.014,
                rear_width=white_key_width * 0.58,
                shoulder_y=-0.010,
                left_relief=left_relief,
                right_relief=right_relief,
            )
            white_key_mesh_cache[cache_key] = white_key_mesh
        white_key_part = model.part(f"white_key_{index}_part")
        white_key_part.visual(
            white_key_mesh,
            origin=Origin(xyz=(0.000, -0.018, 0.001)),
            material=key_white,
            name="white_key",
        )
        white_key_part.inertial = Inertial.from_geometry(
            Box((white_key_width * 0.92, 0.080, 0.014)),
            mass=0.043,
            origin=Origin(xyz=(0.000, -0.018, 0.008)),
        )
        model.articulation(
            f"chassis_to_white_key_{index}",
            ArticulationType.PRISMATIC,
            parent=chassis,
            child=white_key_part,
            origin=Origin(xyz=(center_x, -0.026, 0.019)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=2.0,
                velocity=0.08,
                lower=0.0,
                upper=0.0045,
            ),
        )

    black_key_mesh = _write_black_key_mesh("midi_black_key.obj")
    for visual_index, white_index in enumerate(sorted(black_key_positions)):
        key_center_x = (white_key_centers[white_index] + white_key_centers[white_index + 1]) / 2.0
        black_key_part = model.part(f"black_key_{visual_index}_part")
        black_key_part.visual(
            Box((0.0086, 0.020, 0.008)),
            origin=Origin(
                xyz=(
                    0.000,
                    -0.010,
                    0.004,
                )
            ),
            material=key_black,
            name="black_key_filler",
        )
        black_key_part.visual(
            black_key_mesh,
            origin=Origin(
                xyz=(
                    0.000,
                    -0.005,
                    0.008,
                )
            ),
            material=key_black,
            name="black_key",
        )
        black_key_part.inertial = Inertial.from_geometry(
            Box((0.0132, 0.047, 0.020)),
            mass=0.028,
            origin=Origin(xyz=(0.000, -0.008, 0.010)),
        )
        model.articulation(
            f"chassis_to_black_key_{visual_index}",
            ArticulationType.PRISMATIC,
            parent=chassis,
            child=black_key_part,
            origin=Origin(xyz=(key_center_x, -0.004, 0.026)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=1.8,
                velocity=0.08,
                lower=0.0,
                upper=0.0032,
            ),
        )

    def _mount_to_chassis_surface(
        child_part,
        *,
        articulation_name: str,
        point_hint: tuple[float, float, float],
        clearance: float = 0.0,
        articulation_type: ArticulationType = ArticulationType.FIXED,
        axis: tuple[float, float, float] | None = None,
        motion_limits: MotionLimits | None = None,
    ) -> None:
        model.articulation(
            articulation_name,
            articulation_type,
            parent=chassis,
            child=child_part,
            origin=place_on_surface(
                child_part,
                rear_housing,
                point_hint=point_hint,
                clearance=clearance,
                asset_root=ASSETS.asset_root,
                prefer_collisions=False,
                child_prefer_collisions=False,
            ),
            axis=axis,
            motion_limits=motion_limits,
        )

    display_part = model.part("display_module")
    display_part.visual(
        Box((0.050, 0.024, 0.006)),
        origin=Origin(xyz=(0.000, 0.000, 0.003)),
        material=display_glass,
        name="display",
    )
    display_part.inertial = Inertial.from_geometry(
        Box((0.050, 0.024, 0.006)),
        mass=0.04,
        origin=Origin(xyz=(0.000, 0.000, 0.003)),
    )
    _mount_to_chassis_surface(
        display_part,
        articulation_name="chassis_to_display_module",
        point_hint=(-0.012, 0.060, 0.080),
    )

    first_knob_part = None
    for row_index, local_y in enumerate((-0.014, 0.014)):
        for column_index, local_x in enumerate((-0.040, -0.010, 0.020, 0.050)):
            knob_part = model.part(f"knob_{row_index}_{column_index}_part")
            knob_part.visual(
                Cylinder(radius=0.008, length=0.010),
                origin=Origin(xyz=(0.000, 0.000, 0.005)),
                material=knob_dark,
                name="knob",
            )
            knob_part.inertial = Inertial.from_geometry(
                Cylinder(radius=0.008, length=0.010),
                mass=0.012,
                origin=Origin(xyz=(0.000, 0.000, 0.005)),
            )
            _mount_to_chassis_surface(
                knob_part,
                articulation_name=f"chassis_to_knob_{row_index}_{column_index}",
                point_hint=(0.055 + local_x, 0.056 + local_y, 0.080),
                articulation_type=ArticulationType.REVOLUTE,
                axis=(0.0, 0.0, 1.0),
                motion_limits=MotionLimits(
                    effort=0.08,
                    velocity=4.0,
                    lower=-2.2,
                    upper=2.2,
                ),
            )
            if first_knob_part is None:
                first_knob_part = knob_part

    first_pad_part = None
    for row_index, local_y in enumerate((-0.014, 0.014)):
        for column_index, local_x in enumerate((0.098, 0.128)):
            pad_part = model.part(f"pad_{row_index}_{column_index}_part")
            pad_part.visual(
                Box((0.024, 0.024, 0.005)),
                origin=Origin(xyz=(0.000, 0.000, 0.0025)),
                material=pad_rubber,
                name="pad",
            )
            pad_part.inertial = Inertial.from_geometry(
                Box((0.024, 0.024, 0.005)),
                mass=0.02,
                origin=Origin(xyz=(0.000, 0.000, 0.0025)),
            )
            _mount_to_chassis_surface(
                pad_part,
                articulation_name=f"chassis_to_pad_{row_index}_{column_index}",
                point_hint=(0.055 + local_x, 0.056 + local_y, 0.080),
                articulation_type=ArticulationType.PRISMATIC,
                axis=(0.0, 0.0, -1.0),
                motion_limits=MotionLimits(
                    effort=8.0,
                    velocity=0.08,
                    lower=0.0,
                    upper=0.0025,
                ),
            )
            if first_pad_part is None:
                first_pad_part = pad_part

    for index, local_x in enumerate((0.066, 0.088, 0.110)):
        button_part = model.part(f"transport_button_{index}_part")
        button_part.visual(
            Box((0.010, 0.026, 0.004)),
            origin=Origin(xyz=(0.000, 0.000, 0.002)),
            material=accent,
            name="transport_button",
        )
        button_part.inertial = Inertial.from_geometry(
            Box((0.010, 0.026, 0.004)),
            mass=0.006,
            origin=Origin(xyz=(0.000, 0.000, 0.002)),
        )
        _mount_to_chassis_surface(
            button_part,
            articulation_name=f"chassis_to_transport_button_{index}",
            point_hint=(0.055 + local_x, 0.024, 0.070),
            articulation_type=ArticulationType.PRISMATIC,
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=5.0,
                velocity=0.08,
                lower=0.0,
                upper=0.0018,
            ),
        )

    pitch_wheel_housing_part = model.part("pitch_wheel_housing_part")
    pitch_wheel_housing_part.visual(
        Box((0.012, 0.032, 0.003)),
        origin=Origin(xyz=(0.000, 0.000, 0.0015)),
        material=deck,
        name="pitch_wheel_floor",
    )
    pitch_wheel_housing_part.visual(
        Box((0.003, 0.032, 0.010)),
        origin=Origin(xyz=(-0.0065, 0.000, 0.005)),
        material=deck,
        name="pitch_wheel_left_cheek",
    )
    pitch_wheel_housing_part.visual(
        Box((0.003, 0.032, 0.010)),
        origin=Origin(xyz=(0.0065, 0.000, 0.005)),
        material=deck,
        name="pitch_wheel_right_cheek",
    )
    pitch_wheel_housing_part.inertial = Inertial.from_geometry(
        Box((0.016, 0.032, 0.010)),
        mass=0.012,
        origin=Origin(xyz=(0.000, 0.000, 0.005)),
    )
    _mount_to_chassis_surface(
        pitch_wheel_housing_part,
        articulation_name="chassis_to_pitch_wheel_housing",
        point_hint=(-0.224, 0.026, 0.070),
    )

    pitch_wheel_part = model.part("pitch_wheel_part")
    pitch_wheel_part.visual(
        Cylinder(radius=0.011, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.007), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=wheel_rubber,
        name="pitch_wheel",
    )
    pitch_wheel_part.inertial = Inertial.from_geometry(
        Cylinder(radius=0.011, length=0.010),
        mass=0.02,
        origin=Origin(xyz=(0.000, 0.000, 0.012)),
    )
    _mount_to_chassis_surface(
        pitch_wheel_part,
        articulation_name="chassis_to_pitch_wheel",
        point_hint=(-0.224, 0.026, 0.070),
        articulation_type=ArticulationType.REVOLUTE,
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.2,
            velocity=2.0,
            lower=-0.7,
            upper=0.7,
        ),
    )

    mod_wheel_housing_part = model.part("mod_wheel_housing_part")
    mod_wheel_housing_part.visual(
        Box((0.012, 0.032, 0.003)),
        origin=Origin(xyz=(0.000, 0.000, 0.0015)),
        material=deck,
        name="mod_wheel_floor",
    )
    mod_wheel_housing_part.visual(
        Box((0.003, 0.032, 0.010)),
        origin=Origin(xyz=(-0.0065, 0.000, 0.005)),
        material=deck,
        name="mod_wheel_left_cheek",
    )
    mod_wheel_housing_part.visual(
        Box((0.003, 0.032, 0.010)),
        origin=Origin(xyz=(0.0065, 0.000, 0.005)),
        material=deck,
        name="mod_wheel_right_cheek",
    )
    mod_wheel_housing_part.inertial = Inertial.from_geometry(
        Box((0.016, 0.032, 0.010)),
        mass=0.012,
        origin=Origin(xyz=(0.000, 0.000, 0.005)),
    )
    _mount_to_chassis_surface(
        mod_wheel_housing_part,
        articulation_name="chassis_to_mod_wheel_housing",
        point_hint=(-0.198, 0.026, 0.070),
    )

    mod_wheel_part = model.part("mod_wheel_part")
    mod_wheel_part.visual(
        Cylinder(radius=0.011, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.007), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=wheel_rubber,
        name="mod_wheel",
    )
    mod_wheel_part.inertial = Inertial.from_geometry(
        Cylinder(radius=0.011, length=0.010),
        mass=0.02,
        origin=Origin(xyz=(0.000, 0.000, 0.012)),
    )
    _mount_to_chassis_surface(
        mod_wheel_part,
        articulation_name="chassis_to_mod_wheel",
        point_hint=(-0.198, 0.026, 0.070),
        articulation_type=ArticulationType.REVOLUTE,
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.2,
            velocity=2.0,
            lower=-0.7,
            upper=0.7,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
