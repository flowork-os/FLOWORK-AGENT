# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, all_in_one_printer_with_scanner_lid_and_paper_tray, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: all_in_one_printer_with_scanner_lid_and_paper_tray

from __future__ import annotations

import cadquery as cq
import math
from contextlib import suppress
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from math import cos, pi, sin
from typing import Literal, Optional, Sequence
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

# ===== knobs (9 syms) =====
@dataclass(frozen=True)
class KnobSkirt:
    diameter: float
    height: float
    flare: float = 0.0
    chamfer: float = 0.0

@dataclass(frozen=True)
class KnobGrip:
    style: Literal[
        "none",
        "fluted",
        "scalloped",
        "knurled",
        "ribbed",
        "diamond_knurl",
    ] = "none"
    count: Optional[int] = None
    depth: float = 0.0
    width: Optional[float] = None
    helix_angle_deg: float = 0.0

@dataclass(frozen=True)
class KnobIndicator:
    style: Literal["none", "line", "notch", "wedge", "dot"] = "none"
    length: Optional[float] = None
    width: Optional[float] = None
    depth: float = 0.0
    angle_deg: float = 0.0
    mode: Literal["engraved", "raised"] = "engraved"

@dataclass(frozen=True)
class KnobTopFeature:
    style: Literal["none", "flush_disk", "recessed_disk", "top_insert"] = "none"
    diameter: Optional[float] = None
    depth: float = 0.0
    height: float = 0.0

@dataclass(frozen=True)
class KnobBore:
    style: Literal["none", "round", "d_shaft", "double_d", "splined", "hex"] = "round"
    diameter: Optional[float] = None
    flat_depth: Optional[float] = None
    spline_count: Optional[int] = None
    spline_depth: float = 0.0
    through: bool = True

@dataclass(frozen=True)
class KnobRelief:
    style: Literal["side_window", "top_recess", "coin_slot"]
    angle_deg: float = 0.0
    width: Optional[float] = None
    height: Optional[float] = None
    depth: float = 0.0

def _knobs_loft_between_radii_z(cq_module, radii_and_offsets):
    """Loft a stack of circular sections at given (radius, z-offset) pairs."""
    wp = None
    previous_offset = 0.0
    for radius, offset in radii_and_offsets:
        if wp is None:
            wp = cq_module.Workplane("XY").workplane(offset=offset).circle(radius)
        else:
            wp = wp.workplane(offset=offset - previous_offset).circle(radius)
        previous_offset = offset
    if wp is None:
        raise ValidationError("No loft sections were provided")
    return wp.loft(combine=True, ruled=False)

def _knobs_cut_with_pattern(shape, cutters):
    for cutter in cutters:
        shape = shape.cut(cutter)
    return shape

class KnobGeometry(MeshGeometry):
    """
    Build a flexible rotary knob aligned to local Z with multiple silhouette families.
    """

    def __init__(
        self,
        diameter: float,
        height: float,
        *,
        body_style: Literal[
            "cylindrical",
            "tapered",
            "domed",
            "mushroom",
            "skirted",
            "hourglass",
            "faceted",
            "lobed",
        ] = "cylindrical",
        top_diameter: Optional[float] = None,
        base_diameter: Optional[float] = None,
        crown_radius: float = 0.0,
        edge_radius: float = 0.0,
        side_draft_deg: float = 0.0,
        skirt: Optional[KnobSkirt] = None,
        grip: Optional[KnobGrip] = None,
        indicator: Optional[KnobIndicator] = None,
        top_feature: Optional[KnobTopFeature] = None,
        bore: Optional[KnobBore] = None,
        body_reliefs: Sequence[KnobRelief] = (),
        center: bool = True,
    ):
        super().__init__()
        diameter = float(diameter)
        height = float(height)
        crown_radius = max(0.0, float(crown_radius))
        edge_radius = max(0.0, float(edge_radius))
        side_draft_deg = float(side_draft_deg)
        if diameter <= 0.0 or height <= 0.0:
            raise ValidationError("diameter and height must be positive")
        if abs(side_draft_deg) >= 45.0:
            raise ValidationError("abs(side_draft_deg) must be < 45")

        base_diameter = float(base_diameter) if base_diameter is not None else diameter
        if base_diameter <= 0.0:
            raise ValidationError("base_diameter must be positive")
        top_diameter = float(top_diameter) if top_diameter is not None else diameter
        if top_diameter <= 0.0:
            raise ValidationError("top_diameter must be positive")

        grip = grip or KnobGrip()
        indicator = indicator or KnobIndicator()
        top_feature = top_feature or KnobTopFeature()
        bore = bore or KnobBore(style="none")
        if skirt is not None and (skirt.diameter <= 0.0 or skirt.height <= 0.0):
            raise ValidationError("KnobSkirt diameter and height must be positive")
        if grip.depth < 0.0:
            raise ValidationError("KnobGrip.depth must be non-negative")
        if indicator.depth < 0.0:
            raise ValidationError("KnobIndicator.depth must be non-negative")
        if top_feature.depth < 0.0 or top_feature.height < 0.0:
            raise ValidationError("KnobTopFeature depth/height must be non-negative")
        if bore.diameter is not None and bore.diameter <= 0.0:
            raise ValidationError("KnobBore.diameter must be positive when provided")
        for relief in body_reliefs:
            if relief.depth < 0.0:
                raise ValidationError("KnobRelief.depth must be non-negative")

        body_height = height
        body_bottom = -height * 0.5
        max_radius = max(base_diameter, top_diameter) * 0.5
        if skirt is not None:
            max_radius = max(max_radius, skirt.diameter * 0.5)

        def body_radius_at(t: float) -> float:
            if body_style == "cylindrical":
                return max(base_diameter, top_diameter) * 0.5
            if body_style == "tapered":
                return (base_diameter * (1.0 - t) + top_diameter * t) * 0.5
            if body_style == "domed":
                if t < 0.72:
                    return (base_diameter * 0.5) * (
                        1.0 - min(max(side_draft_deg / 50.0, -0.2), 0.2) * t
                    )
                u = (t - 0.72) / 0.28
                return max(
                    0.001,
                    top_diameter * 0.5 + (base_diameter * 0.5 - top_diameter * 0.5) * (1.0 - u * u),
                )
            if body_style == "mushroom":
                stem_radius = min(base_diameter, top_diameter, diameter) * 0.28
                cap_radius = max(base_diameter, top_diameter, diameter) * 0.5
                if t < 0.42:
                    return stem_radius
                if t < 0.62:
                    u = (t - 0.42) / 0.20
                    return stem_radius + (cap_radius - stem_radius) * u
                if t < 0.85:
                    return cap_radius
                u = (t - 0.85) / 0.15
                return max(cap_radius * (1.0 - 0.20 * u * u), stem_radius)
            if body_style == "skirted":
                skirt_radius = max(base_diameter * 0.55, diameter * 0.52)
                crown_radius_local = top_diameter * 0.5
                if t < 0.40:
                    return skirt_radius
                if t < 0.56:
                    u = (t - 0.40) / 0.16
                    return skirt_radius + (crown_radius_local - skirt_radius) * u
                return crown_radius_local
            if body_style == "hourglass":
                waist_radius = min(base_diameter, top_diameter, diameter) * 0.32
                if t < 0.5:
                    u = t / 0.5
                    return base_diameter * 0.5 + (waist_radius - base_diameter * 0.5) * u
                u = (t - 0.5) / 0.5
                return waist_radius + (top_diameter * 0.5 - waist_radius) * u
            if body_style == "faceted":
                return (base_diameter * (1.0 - t) + top_diameter * t) * 0.5
            if body_style == "lobed":
                lower_radius = base_diameter * 0.5
                upper_radius = max(top_diameter, diameter * 1.02) * 0.5
                if t < 0.24:
                    u = t / 0.24
                    return lower_radius + (upper_radius * 0.92 - lower_radius) * u
                if t < 0.80:
                    u = (t - 0.24) / 0.56
                    return upper_radius * (0.92 + 0.08 * sin(u * pi))
                u = (t - 0.80) / 0.20
                return upper_radius + (top_diameter * 0.5 - upper_radius) * u
            raise ValidationError(f"Unsupported body_style {body_style!r}")

        def section_outline(radius: float, t: float):
            if body_style == "faceted":
                facet_count = 6
                phase = pi / float(facet_count)
                return [
                    (
                        radius * cos(phase + 2.0 * pi * index / float(facet_count)),
                        radius * sin(phase + 2.0 * pi * index / float(facet_count)),
                    )
                    for index in range(facet_count)
                ]
            if body_style == "lobed":
                lobe_count = 5
                point_count = 72
                blend = min(max((t - 0.10) / 0.30, 0.0), 1.0)
                amplitude = radius * (0.04 + 0.14 * blend)
                valley_floor = radius * 0.62
                points = []
                for index in range(point_count):
                    theta = 2.0 * pi * index / float(point_count)
                    local_radius = radius - amplitude * (0.5 - 0.5 * cos(lobe_count * theta))
                    local_radius = max(local_radius, valley_floor)
                    points.append((local_radius * cos(theta), local_radius * sin(theta)))
                return points
            return None

        section_offsets = [
            0.0,
            body_height * 0.18,
            body_height * 0.42,
            body_height * 0.72,
            body_height,
        ]
        radii_and_offsets = [
            (max(0.001, body_radius_at(offset / body_height)), body_bottom + offset)
            for offset in section_offsets
        ]
        wp = None
        previous_offset = 0.0
        for radius, offset in radii_and_offsets:
            t = (offset - body_bottom) / body_height if body_height > 1e-9 else 0.0
            profile_points = section_outline(radius, t)
            if wp is None:
                wp = cq.Workplane("XY").workplane(offset=offset)
            else:
                wp = wp.workplane(offset=offset - previous_offset)
            if profile_points is None:
                wp = wp.circle(radius)
            else:
                wp = wp.polyline(profile_points).close()
            previous_offset = offset
        if wp is None:
            raise ValidationError("KnobGeometry requires at least one loft section")
        shape = wp.loft(combine=True, ruled=False)

        if skirt is not None:
            skirt_radius = skirt.diameter * 0.5
            skirt_bottom = body_bottom - skirt.height
            skirt_shape = _knobs_loft_between_radii_z(
                cq,
                [
                    (max(0.001, skirt_radius * (1.0 + skirt.flare)), skirt_bottom),
                    (max(0.001, skirt_radius), body_bottom),
                ],
            )
            shape = shape.union(skirt_shape)
            if skirt.chamfer > 1e-6:
                with suppress(Exception):
                    shape = (
                        shape.faces("<Z")
                        .edges()
                        .chamfer(min(skirt.chamfer, skirt.height * 0.7, skirt_radius * 0.25))
                    )

        if edge_radius > 0.0:
            with suppress(Exception):
                shape = shape.edges("|Z").fillet(min(edge_radius, max_radius * 0.35, height * 0.18))
        if crown_radius > 0.0:
            with suppress(Exception):
                shape = (
                    shape.faces(">Z")
                    .edges()
                    .fillet(min(crown_radius, max_radius * 0.25, height * 0.16))
                )

        if grip.style != "none" and grip.depth > 1e-6:
            grip_count = grip.count or (28 if grip.style in {"knurled", "diamond_knurl"} else 18)
            if grip_count < 2:
                raise ValidationError("KnobGrip.count must be at least 2")
            grip_width = (
                float(grip.width)
                if grip.width is not None
                else (
                    max_radius * 0.18
                    if grip.style in {"fluted", "scalloped"}
                    else max_radius * 0.10
                )
            )
            if grip_width <= 0.0:
                raise ValidationError("KnobGrip.width must be positive when provided")

            cutters = []
            if grip.style in {"fluted", "scalloped", "ribbed"}:
                cutter_radius = grip_width * (0.55 if grip.style != "ribbed" else 0.38)
                radial_center = max_radius + cutter_radius - grip.depth
                for index in range(grip_count):
                    cutter = (
                        cq.Workplane("XY")
                        .circle(cutter_radius)
                        .extrude(
                            height + (skirt.height if skirt is not None else 0.0) + 0.01, both=True
                        )
                        .translate((radial_center, 0.0, body_bottom + height * 0.5))
                        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 360.0 * index / float(grip_count))
                    )
                    cutters.append(cutter)
            else:
                tangential = max(grip_width, max_radius * 0.06)
                radial = max(grip.depth * 1.8, max_radius * 0.06)
                box_height = height * 1.25
                helix_angle = grip.helix_angle_deg if abs(grip.helix_angle_deg) > 1e-6 else 24.0
                for index in range(grip_count):
                    base_angle = 360.0 * index / float(grip_count)
                    for tilt_sign in (-1.0, 1.0) if grip.style == "diamond_knurl" else (1.0,):
                        cutter = (
                            cq.Workplane("XY")
                            .box(radial, tangential, box_height)
                            .translate(
                                (max_radius - grip.depth * 0.5, 0.0, body_bottom + height * 0.5)
                            )
                            .rotate(
                                (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), helix_angle * float(tilt_sign)
                            )
                            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), base_angle)
                        )
                        cutters.append(cutter)
            shape = _knobs_cut_with_pattern(shape, cutters)

        if indicator.style != "none":
            indicator_length = indicator.length or max(diameter * 0.34, 0.003)
            indicator_width = indicator.width or max(diameter * 0.06, 0.0015)
            indicator_depth = max(indicator.depth, max(height * 0.03, 0.0008))
            top_z = body_bottom + height
            if indicator.style in {"line", "notch"}:
                feature = (
                    cq.Workplane("XY")
                    .box(indicator_length, indicator_width, indicator_depth)
                    .translate((indicator_length * 0.18, 0.0, top_z + indicator_depth * 0.5))
                )
            elif indicator.style == "wedge":
                profile = [
                    (-indicator_width * 0.5, 0.0),
                    (indicator_width * 0.5, 0.0),
                    (0.0, indicator_length),
                ]
                feature = (
                    cq.Workplane("XY")
                    .polyline(profile)
                    .close()
                    .extrude(indicator_depth)
                    .translate((0.0, 0.0, top_z))
                )
            else:
                dot_radius = indicator_width * 0.5
                feature = (
                    cq.Workplane("XY")
                    .circle(dot_radius)
                    .extrude(indicator_depth)
                    .translate((indicator_length * 0.22, 0.0, top_z))
                )
            feature = feature.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), indicator.angle_deg)
            if indicator.mode == "raised" and indicator.style != "notch":
                shape = shape.union(feature)
            else:
                shape = shape.cut(feature.translate((0.0, 0.0, -indicator_depth * 0.5)))

        if top_feature.style != "none":
            feature_diameter = top_feature.diameter or diameter * 0.55
            feature_radius = feature_diameter * 0.5
            top_z = body_bottom + height
            if feature_radius <= 0.0:
                raise ValidationError("KnobTopFeature.diameter must be positive when provided")
            if top_feature.style == "flush_disk":
                feature = (
                    cq.Workplane("XY")
                    .circle(feature_radius)
                    .extrude(max(top_feature.height, height * 0.06))
                    .translate((0.0, 0.0, top_z))
                )
                shape = shape.union(feature)
            elif top_feature.style == "top_insert":
                feature = (
                    cq.Workplane("XY")
                    .circle(feature_radius)
                    .extrude(max(top_feature.height, height * 0.04))
                    .translate((0.0, 0.0, top_z + height * 0.01))
                )
                shape = shape.union(feature)
            else:
                feature = (
                    cq.Workplane("XY")
                    .circle(feature_radius)
                    .extrude(max(top_feature.depth, height * 0.08))
                    .translate((0.0, 0.0, top_z - max(top_feature.depth, height * 0.08)))
                )
                shape = shape.cut(feature)

        if bore.style != "none":
            bore_diameter = bore.diameter or diameter * 0.34
            if bore_diameter <= 0.0 or bore_diameter >= max_radius * 2.0:
                raise ValidationError("KnobBore diameter must fit inside the knob body")
            bore_depth = (
                height + (skirt.height if skirt is not None else 0.0) + 0.01
                if bore.through
                else max(height * 0.7, diameter * 0.22)
            )
            if bore.style == "round":
                bore_cut = cq.Workplane("XY").circle(bore_diameter * 0.5).extrude(bore_depth)
            elif bore.style == "hex":
                bore_cut = cq.Workplane("XY").polygon(6, bore_diameter).extrude(bore_depth)
            elif bore.style in {"d_shaft", "double_d"}:
                flat_depth = (
                    float(bore.flat_depth) if bore.flat_depth is not None else bore_diameter * 0.16
                )
                cut_r = bore_diameter * 0.5
                flat_x = cut_r - flat_depth
                circle_points = [
                    (cut_r * cos(theta), cut_r * sin(theta))
                    for theta in (2.0 * pi * index / 48.0 for index in range(48))
                ]
                if bore.style == "d_shaft":
                    profile_points = [(min(point[0], flat_x), point[1]) for point in circle_points]
                else:
                    profile_points = [
                        (max(min(point[0], flat_x), -flat_x), point[1]) for point in circle_points
                    ]
                bore_cut = cq.Workplane("XY").polyline(profile_points).close().extrude(bore_depth)
            else:
                spline_count = bore.spline_count or 8
                if spline_count < 3:
                    raise ValidationError("KnobBore.spline_count must be at least 3")
                spline_depth = max(bore.spline_depth, bore_diameter * 0.06)
                outer_r = bore_diameter * 0.5
                inner_r = max(outer_r - spline_depth, outer_r * 0.72)
                points = []
                for index in range(spline_count * 2):
                    theta = pi * index / float(spline_count)
                    radius = outer_r if index % 2 == 0 else inner_r
                    points.append((radius * cos(theta), radius * sin(theta)))
                bore_cut = cq.Workplane("XY").polyline(points).close().extrude(bore_depth)
            bore_cut = bore_cut.translate(
                (0.0, 0.0, body_bottom - (skirt.height if skirt is not None else 0.0))
            )
            shape = shape.cut(bore_cut)

        for relief in body_reliefs:
            relief_depth = max(relief.depth, diameter * 0.04)
            relief_width = relief.width or diameter * 0.22
            relief_height = relief.height or height * 0.18
            if relief.style == "side_window":
                cutter = (
                    cq.Workplane("XY")
                    .box(relief_depth * 2.2, relief_width, relief_height)
                    .translate((max_radius - relief_depth * 0.55, 0.0, body_bottom + height * 0.55))
                    .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), relief.angle_deg)
                )
                shape = shape.cut(cutter)
            elif relief.style == "top_recess":
                cutter = (
                    cq.Workplane("XY")
                    .circle(relief_width * 0.5)
                    .extrude(relief_depth)
                    .translate((0.0, 0.0, body_bottom + height - relief_depth))
                )
                shape = shape.cut(cutter)
            else:
                cutter = (
                    cq.Workplane("XY")
                    .box(relief_width, relief_width * 0.24, relief_depth)
                    .translate((0.0, 0.0, body_bottom + height - relief_depth * 0.5))
                    .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), relief.angle_deg)
                )
                shape = shape.cut(cutter)

        solid = _to_shape(shape)
        if not center:
            bb = solid.BoundingBox()
            solid = solid.translate(cq.Vector(0.0, 0.0, -bb.zmin))
        self._set(solid)

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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
import cadquery as cq
BODY_W = 0.44
BODY_D = 0.36
BODY_H = 0.18
DECK_Z = 0.162
FRONT_TOP_Z = 0.112
CONTROL_Y_REAR = 0.070
CONTROL_Y_FRONT = BODY_D / 2
CONTROL_SLOPE = math.atan2(DECK_Z - FRONT_TOP_Z, CONTROL_Y_FRONT - CONTROL_Y_REAR)
SCANNER_W = 0.322
SCANNER_D = 0.226
SCANNER_CAVITY_Y = -0.052
SCANNER_FLOOR_Z = 0.084
LID_W = 0.342
LID_D = 0.246
LID_T = 0.024
LID_HINGE_Y = -BODY_D / 2 + 0.018
LID_HINGE_Z = DECK_Z - 0.004
TRAY_W = 0.310
TRAY_D = 0.192
TRAY_FLOOR_T = 0.0035
TRAY_WALL_T = 0.0035
TRAY_WALL_H = 0.034
TRAY_FRONT_H = 0.048
TRAY_FRONT_LIP = 0.010
TRAY_ORIGIN_Y = BODY_D / 2 - 0.013
TRAY_ORIGIN_Z = 0.012
TRAY_TRAVEL = 0.092
SHELF_W = 0.286
SHELF_D = 0.094
SHELF_T = 0.0035
SHELF_RAIL_H = 0.015
SHELF_RAIL_T = 0.0035
SHELF_FRONT_LIP_H = 0.012
SHELF_HINGE_Y = BODY_D / 2 - 0.004
SHELF_HINGE_Z = 0.075
KEY_W = 0.012
KEY_D = 0.008
KEY_H = 0.0034
KEY_TRAVEL = 0.0024
KEY_POSITIONS = (
    (-0.062, 0.140),
    (-0.062, 0.126),
    (-0.062, 0.112),
    (0.066, 0.140),
    (0.066, 0.126),
    (0.066, 0.112),
)
DIAL_X = 0.122
DIAL_Y = 0.126
DIAL_D = 0.022
DIAL_H = 0.010
def strip_surface_point(x: float, y: float, proud: float = 0.0) -> tuple[float, float, float]:
    span = (y - CONTROL_Y_REAR) / (CONTROL_Y_FRONT - CONTROL_Y_REAR)
    z = DECK_Z + span * (FRONT_TOP_Z - DECK_Z)
    return (
        x,
        y + proud * math.sin(CONTROL_SLOPE),
        z + proud * math.cos(CONTROL_SLOPE),
    )
def strip_surface_origin(x: float, y: float, proud: float = 0.0) -> Origin:
    return Origin(
        xyz=strip_surface_point(x, y, proud=proud),
        rpy=(-CONTROL_SLOPE, 0.0, 0.0),
    )
def make_body_shape() -> cq.Workplane:
    side_profile = [
        (-BODY_D / 2, 0.0),
        (BODY_D / 2, 0.0),
        (BODY_D / 2, FRONT_TOP_Z),
        (CONTROL_Y_REAR, DECK_Z),
        (-BODY_D / 2, DECK_Z),
    ]
    outer = (
        cq.Workplane("YZ")
        .polyline(side_profile)
        .close()
        .extrude(BODY_W)
        .translate((-BODY_W / 2, 0.0, 0.0))
    )

    scanner_cut = (
        cq.Workplane("XY")
        .box(SCANNER_W, SCANNER_D, BODY_H, centered=(True, True, False))
        .translate((0.0, SCANNER_CAVITY_Y, SCANNER_FLOOR_Z))
    )
    tray_cut = (
        cq.Workplane("XY")
        .box(0.332, 0.190, 0.058, centered=(True, True, False))
        .translate((0.0, BODY_D / 2 - 0.087, 0.010))
    )
    output_cut = (
        cq.Workplane("XY")
        .box(0.300, 0.090, 0.022, centered=(True, True, False))
        .translate((0.0, BODY_D / 2 - 0.039, 0.080))
    )
    underside_relief = (
        cq.Workplane("XY")
        .box(0.220, 0.160, 0.020, centered=(True, True, False))
        .translate((0.0, 0.005, 0.0))
    )
    return outer.cut(scanner_cut).cut(tray_cut).cut(output_cut).cut(underside_relief)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_all_in_one_printer")

    body_white = model.material("body_white", rgba=(0.92, 0.93, 0.94, 1.0))
    trim_dark = model.material("trim_dark", rgba=(0.18, 0.20, 0.22, 1.0))
    glass_dark = model.material("glass_dark", rgba=(0.18, 0.24, 0.30, 0.85))
    paper_gray = model.material("paper_gray", rgba=(0.78, 0.80, 0.82, 1.0))
    button_gray = model.material("button_gray", rgba=(0.86, 0.87, 0.88, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(make_body_shape(), "body_shell"),
        material=body_white,
        name="body_shell",
    )
    body.visual(
        Box((SCANNER_W - 0.020, SCANNER_D - 0.020, 0.003)),
        origin=Origin(xyz=(0.0, SCANNER_CAVITY_Y, SCANNER_FLOOR_Z + 0.0015)),
        material=glass_dark,
        name="scanner_glass",
    )
    body.visual(
        Box((0.054, 0.030, 0.0025)),
        origin=strip_surface_origin(0.018, 0.126, proud=0.00125),
        material=glass_dark,
        name="display",
    )
    body.visual(
        Cylinder(radius=0.0045, length=BODY_W - 0.110),
        origin=Origin(
            xyz=(0.0, LID_HINGE_Y, LID_HINGE_Z - 0.001),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=trim_dark,
        name="lid_hinge_bar",
    )
    lid = model.part("lid")
    lid.visual(
        Box((LID_W, LID_D - 0.008, 0.004)),
        origin=Origin(xyz=(0.0, LID_D / 2 + 0.004, LID_T - 0.002)),
        material=body_white,
        name="lid_top",
    )
    lid.visual(
        Box((LID_W - 0.020, 0.010, LID_T - 0.004)),
        origin=Origin(xyz=(0.0, LID_D - 0.005, (LID_T - 0.004) / 2)),
        material=body_white,
        name="lid_front",
    )
    lid.visual(
        Box((0.010, LID_D - 0.020, LID_T - 0.004)),
        origin=Origin(
            xyz=(LID_W / 2 - 0.005, LID_D / 2, (LID_T - 0.004) / 2),
        ),
        material=body_white,
        name="lid_side_0",
    )
    lid.visual(
        Box((0.010, LID_D - 0.020, LID_T - 0.004)),
        origin=Origin(
            xyz=(-LID_W / 2 + 0.005, LID_D / 2, (LID_T - 0.004) / 2),
        ),
        material=body_white,
        name="lid_side_1",
    )
    lid.visual(
        Box((LID_W, 0.016, 0.010)),
        origin=Origin(xyz=(0.0, 0.008, 0.005)),
        material=body_white,
        name="lid_rear",
    )
    lid.visual(
        Cylinder(radius=0.0065, length=LID_W - 0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.010), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_dark,
        name="lid_barrel",
    )

    tray = model.part("tray")
    tray.visual(
        Box((TRAY_W, TRAY_D, TRAY_FLOOR_T)),
        origin=Origin(xyz=(0.0, -TRAY_D / 2 + TRAY_FRONT_LIP, TRAY_FLOOR_T / 2)),
        material=paper_gray,
        name="tray_floor",
    )
    tray.visual(
        Box((TRAY_W, TRAY_WALL_T, TRAY_FRONT_H)),
        origin=Origin(xyz=(0.0, -TRAY_WALL_T / 2, TRAY_FRONT_H / 2)),
        material=trim_dark,
        name="tray_front",
    )
    tray.visual(
        Box((TRAY_W, TRAY_WALL_T, TRAY_WALL_H)),
        origin=Origin(
            xyz=(0.0, -TRAY_D + TRAY_WALL_T / 2 + TRAY_FRONT_LIP, TRAY_WALL_H / 2),
        ),
        material=paper_gray,
        name="tray_rear",
    )
    tray.visual(
        Box((TRAY_WALL_T, TRAY_D - TRAY_WALL_T, TRAY_WALL_H)),
        origin=Origin(
            xyz=(
                TRAY_W / 2 - TRAY_WALL_T / 2,
                -TRAY_D / 2 - TRAY_WALL_T / 2 + TRAY_FRONT_LIP / 2,
                TRAY_WALL_H / 2,
            ),
        ),
        material=paper_gray,
        name="tray_side_0",
    )
    tray.visual(
        Box((TRAY_WALL_T, TRAY_D - TRAY_WALL_T, TRAY_WALL_H)),
        origin=Origin(
            xyz=(
                -TRAY_W / 2 + TRAY_WALL_T / 2,
                -TRAY_D / 2 - TRAY_WALL_T / 2 + TRAY_FRONT_LIP / 2,
                TRAY_WALL_H / 2,
            ),
        ),
        material=paper_gray,
        name="tray_side_1",
    )

    shelf = model.part("shelf")
    shelf.visual(
        Box((SHELF_W, SHELF_T, SHELF_D)),
        origin=Origin(xyz=(0.0, SHELF_T / 2, -SHELF_D / 2)),
        material=paper_gray,
        name="shelf_panel",
    )
    shelf.visual(
        Box((SHELF_RAIL_T, SHELF_RAIL_H, SHELF_D - SHELF_T)),
        origin=Origin(
            xyz=(
                SHELF_W / 2 - SHELF_RAIL_T / 2,
                SHELF_RAIL_H / 2,
                -(SHELF_D - SHELF_T) / 2,
            ),
        ),
        material=paper_gray,
        name="shelf_side_0",
    )
    shelf.visual(
        Box((SHELF_RAIL_T, SHELF_RAIL_H, SHELF_D - SHELF_T)),
        origin=Origin(
            xyz=(
                -SHELF_W / 2 + SHELF_RAIL_T / 2,
                SHELF_RAIL_H / 2,
                -(SHELF_D - SHELF_T) / 2,
            ),
        ),
        material=paper_gray,
        name="shelf_side_1",
    )
    shelf.visual(
        Box((SHELF_W, SHELF_FRONT_LIP_H, SHELF_T)),
        origin=Origin(
            xyz=(0.0, SHELF_FRONT_LIP_H / 2, -SHELF_D + SHELF_T / 2),
        ),
        material=paper_gray,
        name="shelf_front_lip",
    )
    shelf.visual(
        Cylinder(radius=0.003, length=SHELF_W - 0.030),
        origin=Origin(xyz=(0.0, 0.003, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_dark,
        name="shelf_barrel",
    )

    model.articulation(
        "body_to_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(0.0, LID_HINGE_Y, LID_HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=1.2, lower=0.0, upper=1.42),
    )
    model.articulation(
        "body_to_tray",
        ArticulationType.PRISMATIC,
        parent=body,
        child=tray,
        origin=Origin(xyz=(0.0, TRAY_ORIGIN_Y, TRAY_ORIGIN_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=0.25, lower=0.0, upper=TRAY_TRAVEL),
    )
    model.articulation(
        "body_to_shelf",
        ArticulationType.REVOLUTE,
        parent=body,
        child=shelf,
        origin=Origin(xyz=(0.0, SHELF_HINGE_Y, SHELF_HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=1.5, lower=0.0, upper=1.48),
    )

    for index, (button_x, button_y) in enumerate(KEY_POSITIONS):
        key = model.part(f"key_{index}")
        key.visual(
            Box((KEY_W, KEY_D, KEY_H)),
            origin=Origin(xyz=(0.0, 0.0, KEY_H / 2)),
            material=button_gray,
            name="key_cap",
        )
        model.articulation(
            f"body_to_key_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=key,
            origin=place_on_surface(
                key,
                body,
                point_hint=strip_surface_point(button_x, button_y, proud=0.010),
                child_axis="+z",
                clearance=0.0,
                up_hint=(1.0, 0.0, 0.0),
            ),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=1.0,
                velocity=0.08,
                lower=0.0,
                upper=KEY_TRAVEL,
            ),
        )

    dial = model.part("menu_dial")
    dial.visual(
        mesh_from_geometry(
            KnobGeometry(
                DIAL_D,
                DIAL_H,
                body_style="cylindrical",
                edge_radius=0.0012,
                grip=KnobGrip(style="fluted", count=16, depth=0.0007),
                indicator=KnobIndicator(style="dot", mode="raised", angle_deg=0.0),
                center=False,
            ),
            "menu_dial",
        ),
        material=trim_dark,
        name="dial_cap",
    )
    model.articulation(
        "body_to_menu_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=place_on_surface(
            dial,
            body,
            point_hint=strip_surface_point(DIAL_X, DIAL_Y, proud=0.012),
            child_axis="+z",
            clearance=0.0,
            up_hint=(1.0, 0.0, 0.0),
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.5, velocity=4.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
