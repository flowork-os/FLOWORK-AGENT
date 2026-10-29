# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from math import cos, pi, sin, sqrt
from typing import Literal, Optional
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

def superellipse_profile(width, height, exponent=2.6, *, segments=48):
    width = float(width); height = float(height); exponent = float(exponent)
    segments = max(12, int(segments))
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    if exponent <= 0:
        raise ValidationError("exponent must be positive")
    a = width * 0.5; b = height * 0.5; power = 2.0 / exponent
    pts = []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        ct = math.cos(t); st = math.sin(t)
        x = a * (abs(ct) ** power); y = b * (abs(st) ** power)
        if ct < 0:
            x = -x
        if st < 0:
            y = -y
        pts.append((x, y))
    return pts

# ===== brackets_hinges_bezels (1 syms) =====
_EPS = 1e-9

# ===== fans (5 syms) =====
def _fans_shift_to_z0(solid):
    """Place the rear-most face on z=0 (sdk center=False behaviour)."""
    bb = solid.BoundingBox()
    return solid.translate(cq.Vector(0.0, 0.0, -bb.zmin))

@dataclass(frozen=True)
class FanRotorBlade:
    shape: Literal["straight", "scimitar", "broad", "narrow"] = "straight"
    tip_pitch_deg: Optional[float] = None
    camber: float = 0.0
    tip_clearance: float = 0.0

@dataclass(frozen=True)
class FanRotorHub:
    style: Literal["flat", "domed", "capped", "spinner"] = "domed"
    rear_collar_height: Optional[float] = None
    rear_collar_radius: Optional[float] = None
    bore_diameter: Optional[float] = None

@dataclass(frozen=True)
class FanRotorShroud:
    thickness: float
    depth: Optional[float] = None
    clearance: float = 0.0
    lip_depth: float = 0.0

class FanRotorGeometry(MeshGeometry):
    """
    Build an axial fan rotor with a central hub and pitched blades.
    """

    def __init__(
        self,
        outer_radius: float,
        hub_radius: float,
        blade_count: int,
        *,
        thickness: float,
        blade_pitch_deg: float = 28.0,
        blade_sweep_deg: float = 20.0,
        blade_root_chord: Optional[float] = None,
        blade_tip_chord: Optional[float] = None,
        blade: Optional[FanRotorBlade] = None,
        hub: Optional[FanRotorHub] = None,
        shroud: Optional[FanRotorShroud] = None,
        center: bool = True,
    ):
        super().__init__()
        outer_radius = float(outer_radius)
        hub_radius = float(hub_radius)
        thickness = float(thickness)
        blade_pitch_deg = float(blade_pitch_deg)
        blade_sweep_deg = float(blade_sweep_deg)
        blade_count = int(blade_count)
        blade = blade or FanRotorBlade()
        hub = hub or FanRotorHub()

        if outer_radius <= 0.0 or hub_radius <= 0.0 or thickness <= 0.0:
            raise ValueError("outer_radius, hub_radius, and thickness must be positive")
        if blade_count < 2:
            raise ValueError("blade_count must be at least 2")
        if hub_radius >= outer_radius:
            raise ValueError("hub_radius must be less than outer_radius")
        if abs(blade_pitch_deg) >= 85.0:
            raise ValueError("abs(blade_pitch_deg) must be < 85")
        if abs(blade_sweep_deg) >= 85.0:
            raise ValueError("abs(blade_sweep_deg) must be < 85")

        radial_span = outer_radius - hub_radius
        root_chord = (
            float(blade_root_chord)
            if blade_root_chord is not None
            else max(radial_span * 0.32, thickness * 1.5)
        )
        tip_chord = (
            float(blade_tip_chord)
            if blade_tip_chord is not None
            else max(radial_span * 0.20, thickness * 1.2)
        )
        if root_chord <= 0.0 or tip_chord <= 0.0:
            raise ValueError("blade_root_chord and blade_tip_chord must be positive")
        if max(root_chord, tip_chord) >= outer_radius * 1.6:
            raise ValueError("blade chords are too large for the rotor envelope")

        blade_shape = str(blade.shape)
        if blade_shape not in {"straight", "scimitar", "broad", "narrow"}:
            raise ValueError("blade.shape must be one of straight, scimitar, broad, or narrow")
        hub_style = str(hub.style)
        if hub_style not in {"flat", "domed", "capped", "spinner"}:
            raise ValueError("hub.style must be one of flat, domed, capped, or spinner")

        tip_pitch_deg = (
            float(blade.tip_pitch_deg)
            if blade.tip_pitch_deg is not None
            else blade_pitch_deg * 0.56
        )
        if abs(tip_pitch_deg) >= 85.0:
            raise ValueError("abs(blade.tip_pitch_deg) must be < 85")
        camber = float(blade.camber)
        if abs(camber) > 0.50:
            raise ValueError("abs(blade.camber) must be <= 0.5")
        tip_clearance = float(blade.tip_clearance)
        if tip_clearance < 0.0:
            raise ValueError("blade.tip_clearance must be non-negative")

        shroud_thickness = 0.0
        shroud_depth = 0.0
        ring_inner_radius: Optional[float] = None
        ring_outer_radius: Optional[float] = None
        shroud_lip_depth = 0.0
        if shroud is not None:
            shroud_thickness = float(shroud.thickness)
            shroud_depth = (
                float(shroud.depth) if shroud.depth is not None else max(thickness * 0.80, 1.0e-4)
            )
            shroud_clearance = float(shroud.clearance)
            shroud_lip_depth = float(shroud.lip_depth)
            if shroud_thickness <= 0.0:
                raise ValueError("shroud.thickness must be positive")
            if shroud_depth <= 0.0:
                raise ValueError("shroud.depth must be positive")
            if shroud_clearance < 0.0:
                raise ValueError("shroud.clearance must be non-negative")
            if shroud_lip_depth < 0.0:
                raise ValueError("shroud.lip_depth must be non-negative")
            if tip_clearance > 1.0e-9:
                raise ValueError("blade.tip_clearance cannot be used with shroud")
            ring_outer_radius = outer_radius - shroud_clearance
            ring_inner_radius = ring_outer_radius - shroud_thickness
            if ring_outer_radius <= 0.0 or ring_inner_radius <= 0.0:
                raise ValueError("shroud dimensions exceed the rotor envelope")
            if ring_inner_radius <= hub_radius + max(thickness * 0.25, 1.0e-4):
                raise ValueError("shroud leaves no usable blade span")

        def lerp(a: float, b: float, t: float) -> float:
            return float(a) + (float(b) - float(a)) * float(t)

        def chord_scale(t: float) -> float:
            if blade_shape == "straight":
                return 1.00
            if blade_shape == "scimitar":
                return 1.08 - 0.16 * t + 0.05 * sin(pi * t)
            if blade_shape == "broad":
                return 1.05 + 0.10 * sin(pi * t) - 0.03 * t
            return 0.92 - 0.12 * t

        def sweep_factor(t: float) -> float:
            if blade_shape == "straight":
                return t
            if blade_shape == "scimitar":
                return min(1.25, 0.52 * t + 0.76 * t * t)
            if blade_shape == "broad":
                return min(1.08, 0.82 * t + 0.22 * sin(pi * t))
            return 0.82 * t

        def rotate_section_points(
            points: list,
            angle_rad: float,
        ) -> list:
            c = cos(angle_rad)
            s = sin(angle_rad)
            return [(y * c - z * s, y * s + z * c) for (y, z) in points]

        def blade_section_points(
            chord: float,
            section_thickness: float,
            pitch_deg: float,
            sweep_y: float,
            span_t: float,
        ) -> list:
            half_t = max(section_thickness * 0.5, chord * 0.011)
            camber_amplitude = camber * chord * 0.060
            skew_gain = 0.0
            if blade_shape == "scimitar":
                skew_gain = chord * (0.05 + 0.08 * span_t)
            elif blade_shape == "broad":
                skew_gain = chord * 0.03 * span_t
            elif blade_shape == "narrow":
                skew_gain = -chord * 0.04 * span_t

            upper: list = []
            lower: list = []
            for u in (0.00, 0.10, 0.24, 0.42, 0.62, 0.82, 1.00):
                chord_pos = (u - 0.5) * chord
                thickness_scale = max(0.12, sin(pi * u) ** 0.82)
                thickness_z = half_t * thickness_scale
                camber_z = camber_amplitude * sin(pi * u)
                skew_y = skew_gain * sin(pi * u) * (u - 0.20)
                upper.append((chord_pos + skew_y, camber_z + thickness_z))
                lower.append((chord_pos + skew_y, camber_z - thickness_z * 0.90))

            raw = upper + list(reversed(lower[1:-1]))
            rotated = rotate_section_points(raw, pitch_deg * pi / 180.0)
            return [(sweep_y + y, z) for (y, z) in rotated]

        hub_body_height = thickness * 0.36
        rear_collar_height = (
            float(hub.rear_collar_height)
            if hub.rear_collar_height is not None
            else thickness * 0.18
        )
        rear_collar_radius = (
            float(hub.rear_collar_radius)
            if hub.rear_collar_radius is not None
            else hub_radius * 0.78
        )
        if rear_collar_height < 0.0:
            raise ValueError("hub.rear_collar_height must be non-negative")
        if rear_collar_height > 1.0e-9 and rear_collar_radius <= 0.0:
            raise ValueError("hub.rear_collar_radius must be positive when rear_collar_height > 0")
        if rear_collar_radius >= hub_radius * 1.05:
            raise ValueError("hub.rear_collar_radius must fit within the hub radius")

        hub_body = cq.Workplane("XY").circle(hub_radius).extrude(hub_body_height * 0.5, both=True)
        shape = hub_body
        if rear_collar_height > 1.0e-9:
            rear_collar = (
                cq.Workplane("XY")
                .circle(rear_collar_radius)
                .extrude(rear_collar_height * 0.5, both=True)
                .translate((0.0, 0.0, -thickness * 0.24))
            )
            shape = shape.union(rear_collar)

        if hub_style == "capped":
            front_cap = (
                cq.Workplane("XY")
                .circle(hub_radius * 0.82)
                .extrude(max(thickness * 0.18, 1.0e-4))
                .translate((0.0, 0.0, hub_body_height * 0.5))
            )
            shape = shape.union(front_cap)
        elif hub_style in {"domed", "spinner"}:
            front_cap_height = thickness * (0.34 if hub_style == "domed" else 0.52)
            front_top_radius = hub_radius * (0.40 if hub_style == "domed" else 0.05)
            front_cap = (
                cq.Workplane("XY")
                .workplane(offset=hub_body_height * 0.5)
                .circle(hub_radius * 0.92)
                .workplane(offset=front_cap_height)
                .circle(max(front_top_radius, 1.0e-4))
                .loft(combine=True, ruled=False)
            )
            shape = shape.union(front_cap)

        if hub.bore_diameter is not None:
            bore_diameter = float(hub.bore_diameter)
            if bore_diameter <= 0.0:
                raise ValueError("hub.bore_diameter must be positive")
            bore_radius = bore_diameter * 0.5
            bore_limit = min(
                hub_radius, rear_collar_radius if rear_collar_height > 0.0 else hub_radius
            )
            if bore_radius >= bore_limit * 0.92:
                raise ValueError("hub.bore_diameter is too large for the hub")
            bore = (
                cq.Workplane("XY")
                .circle(bore_radius)
                .extrude(
                    max(thickness * 1.8, hub_body_height + rear_collar_height + shroud_depth),
                    both=True,
                )
            )
            shape = shape.cut(bore)

        root_radius = hub_radius * 0.82
        if shroud is not None:
            assert ring_inner_radius is not None
            tip_bridge = min(shroud_thickness * 0.18, max(thickness * 0.05, 5.0e-4))
            tip_radius = ring_inner_radius + tip_bridge
        else:
            tip_radius = outer_radius - tip_clearance
        if tip_radius <= root_radius + max(thickness * 0.22, 1.0e-4):
            raise ValueError("blade.tip_clearance leaves no usable blade span")

        blade_span = tip_radius - root_radius
        station_fracs = (0.00, 0.18, 0.42, 0.70, 1.00)
        stations = [root_radius + blade_span * frac for frac in station_fracs]
        section_chords = [
            lerp(root_chord, tip_chord, frac) * chord_scale(frac) for frac in station_fracs
        ]
        root_pitch_deg = blade_pitch_deg * 1.16
        section_pitches = [
            lerp(root_pitch_deg, tip_pitch_deg, frac**0.82) for frac in station_fracs
        ]
        root_section_t = max(thickness * 0.18, root_chord * 0.080)
        tip_section_t = max(thickness * 0.08, tip_chord * 0.048)
        thickness_shape_scale = {
            "straight": 1.00,
            "scimitar": 0.94,
            "broad": 1.08,
            "narrow": 0.88,
        }[blade_shape]
        section_thicknesses = [
            lerp(root_section_t, tip_section_t, frac**0.78) * thickness_shape_scale
            for frac in station_fracs
        ]
        sweep_amount = blade_span * sin(blade_sweep_deg * pi / 180.0) * 0.34
        section_sweeps = [sweep_amount * sweep_factor(frac) for frac in station_fracs]

        blade_wp = None
        previous_station = 0.0
        for station, chord, section_t, pitch_deg, sweep_y, span_t in zip(
            stations,
            section_chords,
            section_thicknesses,
            section_pitches,
            section_sweeps,
            station_fracs,
        ):
            section = blade_section_points(chord, section_t, pitch_deg, sweep_y, span_t)
            if blade_wp is None:
                blade_wp = cq.Workplane("YZ").workplane(offset=station).polyline(section).close()
            else:
                blade_wp = (
                    blade_wp.workplane(offset=station - previous_station).polyline(section).close()
                )
            previous_station = station
        assert blade_wp is not None
        blade_solid = blade_wp.loft(combine=True, ruled=False)

        angle_step = 360.0 / float(blade_count)
        for blade_index in range(blade_count):
            shape = shape.union(
                blade_solid.rotate(
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0),
                    angle_step * float(blade_index),
                )
            )

        if shroud is not None:
            assert ring_outer_radius is not None
            assert ring_inner_radius is not None
            tip_ring = (
                cq.Workplane("XY")
                .circle(ring_outer_radius)
                .circle(ring_inner_radius)
                .extrude(shroud_depth * 0.5, both=True)
            )
            shape = shape.union(tip_ring)
            if shroud_lip_depth > 1.0e-9:
                front_lip = (
                    cq.Workplane("XY")
                    .workplane(offset=shroud_depth * 0.5)
                    .circle(ring_outer_radius)
                    .circle(ring_inner_radius)
                    .extrude(shroud_lip_depth)
                )
                shape = shape.union(front_lip)

        solid = _to_shape(shape)
        if not center:
            solid = _fans_shift_to_z0(solid)
        self._set(solid)

# ===== primitives (1 syms) =====
class CapsuleGeometry(MeshGeometry):
    def __init__(self, radius, length, *, radial_segments=24, height_segments=8):
        super().__init__()
        radius = float(radius)
        length = float(length)
        if radius <= 0.0:
            raise ValidationError("radius must be positive")
        if length < 0.0:
            raise ValidationError("length must be non-negative")

        sphere = cq.Solid.makeSphere(
            radius, angleDegrees1=-90, angleDegrees2=90, angleDegrees3=360
        )
        if length <= 1e-9:
            self._set(sphere)
            return

        half = length / 2.0
        # cylindrical body of height `length` centered, hemispherical caps at +-half
        body = cq.Solid.makeCylinder(
            radius, length, cq.Vector(0, 0, -half), cq.Vector(0, 0, 1)
        )
        top = sphere.translate(cq.Vector(0, 0, half))
        bottom = sphere.translate(cq.Vector(0, 0, -half))
        solid = body.fuse(top, bottom)
        try:
            solid = solid.clean()
        except Exception:
            pass
        self._set(solid)

# ===== sweeps (24 syms) =====
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

def superellipse_side_loft(sections, *, exponents=2.8, segments: int = 56, cap: bool = True,
                           closed: bool = True, min_height: float = 1e-4, min_width: float = 1e-4):
    """Build an organic casing from side-profile rails ``(y, z_min, z_max, width)``.

    The loft axis is +Y and each cross-section is a superellipse in XZ. Profile
    construction is verbatim from the sdk; the rings are stitched into a ruled
    B-rep loft (matching LoftGeometry's quad strips) and rotated into the +Y
    world frame."""
    if len(sections) < 2:
        raise ValueError("superellipse_side_loft requires at least two sections")

    if isinstance(exponents, (int, float)):
        expo_list = [float(exponents)] * len(sections)
    else:
        expo_list = [float(v) for v in exponents]
        if len(expo_list) != len(sections):
            raise ValueError("exponents must match section count")

    profiles = []
    segs = max(12, int(segments))
    min_h = max(1e-9, float(min_height))
    min_w = max(1e-9, float(min_width))

    for i, sec in enumerate(sections):
        y, z_min, z_max, width = sec
        y = float(y)
        z0 = float(z_min)
        z1 = float(z_max)
        if z1 < z0:
            z0, z1 = z1, z0

        height = max(min_h, z1 - z0)
        width = max(min_w, float(width))
        z_center = 0.5 * (z0 + z1)
        exponent = max(0.2, float(expo_list[i]))

        prof_xy = superellipse_profile(width, height, exponent=exponent, segments=segs)
        # Map final (x, y_section, z) into the loft frame: (x, -(z_local + z_center), y).
        prof_xyz = [(x, -(z_local + z_center), y) for (x, z_local) in prof_xy]
        profiles.append(prof_xyz)

    solid = _loft_section_solid(profiles, ruled=True)
    # rotate_x(-pi/2) to bring the loft axis to world +Y (matches sdk geom.rotate_x).
    geom = MeshGeometry()._set(solid)
    geom.rotate((1.0, 0.0, 0.0), -pi / 2.0)
    return geom

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
def _mat(model: ArticulatedObject, name: str, rgba: tuple[float, float, float, float]) -> Material:
    return model.material(name, rgba=rgba)
def _envelope_mesh():
    sections = [
        (-15.0, -0.20, 0.20, 0.35),
        (-14.0, -1.40, 1.55, 2.25),
        (-12.2, -2.85, 3.00, 5.25),
        (-9.0, -3.70, 3.85, 7.45),
        (-4.5, -4.10, 4.15, 8.35),
        (0.0, -4.25, 4.25, 8.70),
        (4.8, -4.05, 4.10, 8.30),
        (9.4, -3.25, 3.45, 6.75),
        (12.4, -1.90, 2.10, 3.90),
        (14.3, -0.62, 0.72, 1.15),
        (15.0, -0.14, 0.14, 0.30),
    ]
    geom = superellipse_side_loft(sections, exponents=2.25, segments=72)
    # The side-loft helper runs along local +Y; rotate it so the airship's
    # longitudinal axis is world +X and the nose points forward.
    geom.rotate_z(-math.pi / 2.0)
    return geom
def _gondola_mesh():
    sections = [
        (-2.70, -0.38, 0.32, 0.90),
        (-2.25, -0.72, 0.62, 1.85),
        (-1.25, -0.82, 0.72, 2.30),
        (0.85, -0.82, 0.72, 2.38),
        (2.10, -0.68, 0.58, 1.90),
        (2.65, -0.32, 0.28, 0.80),
    ]
    geom = superellipse_side_loft(sections, exponents=3.2, segments=36)
    geom.rotate_z(-math.pi / 2.0)
    return geom
def _support_struts_mesh():
    geom = MeshGeometry()
    struts = [
        ((-1.95, -0.90, -3.72), (-1.18, -0.82, -4.56)),
        ((-1.95, 0.90, -3.72), (-1.18, 0.82, -4.56)),
        ((1.95, -0.90, -3.72), (1.18, -0.82, -4.56)),
        ((1.95, 0.90, -3.72), (1.18, 0.82, -4.56)),
        ((-1.40, 0.0, -3.88), (1.40, 0.0, -4.50)),
    ]
    for a, b in struts:
        geom.merge(
            wire_from_points(
                [a, b],
                radius=0.075,
                radial_segments=14,
                cap_ends=True,
            )
        )
    return geom
def _rotor_mesh(name: str):
    rotor = FanRotorGeometry(
        outer_radius=0.58,
        hub_radius=0.15,
        blade_count=5,
        thickness=0.085,
        blade_pitch_deg=30.0,
        blade_sweep_deg=24.0,
        blade=FanRotorBlade(shape="scimitar", tip_pitch_deg=12.0, camber=0.18),
        hub=FanRotorHub(style="spinner", bore_diameter=0.055),
    )
    return mesh_from_geometry(rotor, name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="utility_blimp")

    fabric = _mat(model, "warm_gray_fabric", (0.76, 0.77, 0.72, 1.0))
    seam = _mat(model, "darker_fabric_seams", (0.38, 0.40, 0.38, 1.0))
    frame = _mat(model, "dark_anodized_frame", (0.08, 0.09, 0.10, 1.0))
    cabin = _mat(model, "matte_utility_blue", (0.12, 0.20, 0.27, 1.0))
    glass = _mat(model, "smoked_glass", (0.03, 0.07, 0.09, 0.72))
    tail_mat = _mat(model, "tail_fabric_panel", (0.58, 0.61, 0.56, 1.0))
    pod_mat = _mat(model, "engine_pod_gray", (0.28, 0.30, 0.31, 1.0))
    prop_mat = _mat(model, "black_composite", (0.015, 0.015, 0.014, 1.0))

    hull = model.part("hull")
    hull.visual(
        mesh_from_geometry(_envelope_mesh(), "thick_envelope"),
        material=fabric,
        name="envelope",
    )
    hull.visual(
        Cylinder(radius=0.035, length=22.0),
        origin=Origin(xyz=(0.0, -4.38, -0.02), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=seam,
        name="port_belly_seam",
    )
    hull.visual(
        Cylinder(radius=0.035, length=22.0),
        origin=Origin(xyz=(0.0, 4.38, -0.02), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=seam,
        name="starboard_belly_seam",
    )
    hull.visual(
        mesh_from_geometry(_support_struts_mesh(), "gondola_support_struts"),
        material=frame,
        name="gondola_struts",
    )
    # Boxy cruciform stabilizers are fixed to the rear of the envelope.
    hull.visual(
        Box((3.2, 0.36, 2.65)),
        origin=Origin(xyz=(-13.18, 0.0, 3.95)),
        material=tail_mat,
        name="upper_fin",
    )
    hull.visual(
        Box((2.7, 0.34, 2.05)),
        origin=Origin(xyz=(-13.05, 0.0, -3.10)),
        material=tail_mat,
        name="lower_fin",
    )
    hull.visual(
        Box((3.2, 3.15, 0.28)),
        origin=Origin(xyz=(-13.18, 3.65, 0.22)),
        material=tail_mat,
        name="port_tailplane",
    )
    hull.visual(
        Box((3.2, 3.15, 0.28)),
        origin=Origin(xyz=(-13.18, -3.65, 0.22)),
        material=tail_mat,
        name="starboard_tailplane",
    )

    gondola = model.part("gondola")
    gondola.visual(
        mesh_from_geometry(_gondola_mesh(), "compact_gondola_shell"),
        material=cabin,
        name="gondola_shell",
    )
    gondola.visual(
        Box((0.95, 0.035, 0.42)),
        origin=Origin(xyz=(1.30, 1.155, 0.20)),
        material=glass,
        name="port_window_0",
    )
    gondola.visual(
        Box((0.95, 0.035, 0.42)),
        origin=Origin(xyz=(-0.05, 1.155, 0.22)),
        material=glass,
        name="port_window_1",
    )
    gondola.visual(
        Box((0.95, 0.035, 0.42)),
        origin=Origin(xyz=(1.30, -1.155, 0.20)),
        material=glass,
        name="starboard_window_0",
    )
    gondola.visual(
        Box((0.95, 0.035, 0.42)),
        origin=Origin(xyz=(-0.05, -1.155, 0.22)),
        material=glass,
        name="starboard_window_1",
    )
    gondola.visual(
        Box((1.05, 0.045, 0.50)),
        origin=Origin(xyz=(2.18, 0.0, 0.17), rpy=(0.0, 0.0, 0.0)),
        material=glass,
        name="front_windscreen",
    )
    gondola.visual(
        Box((2.85, 1.88, 0.16)),
        origin=Origin(xyz=(0.0, 0.0, 0.78)),
        material=frame,
        name="roof_hardpoints",
    )
    gondola.visual(
        Box((5.10, 0.12, 0.16)),
        origin=Origin(xyz=(0.0, 1.26, -0.48)),
        material=frame,
        name="port_skid_rail",
    )
    gondola.visual(
        Box((5.10, 0.12, 0.16)),
        origin=Origin(xyz=(0.0, -1.26, -0.48)),
        material=frame,
        name="starboard_skid_rail",
    )
    for bracket_x in (-1.85, 1.85):
        gondola.visual(
            Box((0.18, 0.34, 0.55)),
            origin=Origin(xyz=(bracket_x, 1.16, -0.25)),
            material=frame,
            name=f"port_skid_bracket_{bracket_x:+.0f}".replace("+", "p").replace("-", "n"),
        )
        gondola.visual(
            Box((0.18, 0.34, 0.55)),
            origin=Origin(xyz=(bracket_x, -1.16, -0.25)),
            material=frame,
            name=f"starboard_skid_bracket_{bracket_x:+.0f}".replace("+", "p").replace("-", "n"),
        )
    model.articulation(
        "hull_to_gondola",
        ArticulationType.FIXED,
        parent=hull,
        child=gondola,
        origin=Origin(xyz=(0.0, 0.0, -5.34)),
    )

    for side_name, side in (("port", 1.0), ("starboard", -1.0)):
        pylon = model.part(f"{side_name}_pylon")
        pylon.visual(
            Box((0.52, 0.16, 0.46)),
            origin=Origin(xyz=(0.0, 0.0, 0.25)),
            material=frame,
            name="side_mount",
        )
        pylon.visual(
            Cylinder(radius=0.105, length=1.32),
            origin=Origin(xyz=(0.0, side * 0.66, 0.02), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=frame,
            name="pylon_tube",
        )
        pylon.visual(
            Box((0.34, 0.22, 0.24)),
            origin=Origin(xyz=(0.0, side * 1.34, 0.17)),
            material=frame,
            name="upper_yoke_lug",
        )
        pylon.visual(
            Box((0.34, 0.22, 0.24)),
            origin=Origin(xyz=(0.0, side * 1.34, -0.17)),
            material=frame,
            name="lower_yoke_lug",
        )
        model.articulation(
            f"gondola_to_{side_name}_pylon",
            ArticulationType.FIXED,
            parent=gondola,
            child=pylon,
            origin=Origin(xyz=(-1.40, side * 1.232, -0.20)),
        )

        pod = model.part(f"{side_name}_pod")
        pod.visual(
            mesh_from_geometry(CapsuleGeometry(0.43, 1.20, radial_segments=32), f"{side_name}_pod_nacelle"),
            origin=Origin(xyz=(0.0, side * 0.56, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=pod_mat,
            name="nacelle",
        )
        pod.visual(
            Cylinder(radius=0.18, length=0.34),
            origin=Origin(xyz=(0.0, side * 0.04, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=frame,
            name="pivot_socket",
        )
        pod.visual(
            Cylinder(radius=0.075, length=0.18),
            origin=Origin(xyz=(1.03, side * 0.56, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=frame,
            name="shaft_boss",
        )
        model.articulation(
            f"{side_name}_pylon_to_pod",
            ArticulationType.REVOLUTE,
            parent=pylon,
            child=pod,
            origin=Origin(xyz=(0.0, side * 1.34, 0.0)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=280.0, velocity=0.65, lower=-0.55, upper=0.55),
        )

        prop = model.part(f"{side_name}_propeller")
        prop.visual(
            _rotor_mesh(f"{side_name}_propeller_rotor"),
            origin=Origin(xyz=(0.15, side * 0.56, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=prop_mat,
            name="rotor_blades",
        )
        prop.visual(
            Cylinder(radius=0.055, length=0.25),
            origin=Origin(xyz=(0.06, side * 0.56, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=frame,
            name="propeller_shaft",
        )
        model.articulation(
            f"{side_name}_pod_to_propeller",
            ArticulationType.CONTINUOUS,
            parent=pod,
            child=prop,
            origin=Origin(xyz=(1.12, 0.0, 0.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=40.0, velocity=85.0),
        )

    rudder = model.part("rudder")
    rudder.visual(
        Box((1.08, 0.24, 2.18)),
        origin=Origin(xyz=(-0.54, 0.0, 0.0)),
        material=tail_mat,
        name="rudder_panel",
    )
    rudder.visual(
        Cylinder(radius=0.075, length=2.28),
        origin=Origin(xyz=(-0.12, 0.0, 0.0)),
        material=frame,
        name="rudder_hinge_barrel",
    )
    model.articulation(
        "hull_to_rudder",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=rudder,
        origin=Origin(xyz=(-14.78, 0.0, 3.95)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=95.0, velocity=1.2, lower=-0.58, upper=0.58),
    )

    for side_name, side in (("port", 1.0), ("starboard", -1.0)):
        elevator = model.part(f"{side_name}_elevator")
        elevator.visual(
            Box((1.02, 2.92, 0.22)),
            origin=Origin(xyz=(-0.51, 0.0, 0.0)),
            material=tail_mat,
            name="elevator_panel",
        )
        elevator.visual(
            Cylinder(radius=0.065, length=2.98),
            origin=Origin(xyz=(-0.10, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=frame,
            name="elevator_hinge_barrel",
        )
        model.articulation(
            f"hull_to_{side_name}_elevator",
            ArticulationType.REVOLUTE,
            parent=hull,
            child=elevator,
            origin=Origin(xyz=(-14.78, side * 3.65, 0.22)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=90.0, velocity=1.2, lower=-0.45, upper=0.45),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
