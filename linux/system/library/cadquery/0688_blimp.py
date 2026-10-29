# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from math import cos, pi, sin, sqrt
from typing import Literal, Optional
from dataclasses import dataclass, field
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

# ===== section_loft (16 syms) =====
def _cq_shapes():
    """The low-level cadquery shape helpers the real sdk lofts through."""
    from cadquery.occ_impl import shapes as cq_shapes
    return cq_shapes

def _as_vec3(values, *, name):
    if len(values) != 3:
        raise ValidationError("%s must have 3 elements" % name)
    return (float(values[0]), float(values[1]), float(values[2]))

def _normalize_section_points(points, *, name):
    raw = [_as_vec3(point, name=name) for point in points]
    if len(raw) < 3:
        raise ValidationError("%s must contain at least 3 points" % name)

    out = []
    for point in raw:
        if not out or point != out[-1]:
            out.append(point)

    if len(out) >= 2 and out[0] == out[-1]:
        out.pop()

    if len(out) < 3:
        raise ValidationError("%s must contain at least 3 distinct points" % name)
    return out

@dataclass(frozen=True)
class LoftTessellation:
    tolerance: float = 0.001
    angular_tolerance: float = 0.1

    def __post_init__(self):
        if float(self.tolerance) <= 0.0:
            raise ValidationError("tessellation.tolerance must be > 0")
        if float(self.angular_tolerance) <= 0.0:
            raise ValidationError("tessellation.angular_tolerance must be > 0")
        object.__setattr__(self, "tolerance", float(self.tolerance))
        object.__setattr__(self, "angular_tolerance", float(self.angular_tolerance))

@dataclass(frozen=True)
class LoftSection:
    points: tuple

    def __post_init__(self):
        coerced = tuple(_normalize_section_points(self.points, name="section.points"))
        object.__setattr__(self, "points", coerced)

@dataclass(frozen=True)
class SectionLoftSpec:
    sections: tuple
    path: tuple = None
    guide_curves: dict = None
    cap: bool = True
    solid: bool = True
    symmetry: str = None
    ruled: bool = False
    continuity: str = "C2"
    parametrization: str = "uniform"
    degree: int = 3
    compat: bool = True
    smoothing: bool = False
    weights: tuple = (1.0, 1.0, 1.0)
    repair: str = "auto"
    tessellation: LoftTessellation = field(default_factory=LoftTessellation)

    def __post_init__(self):
        sections = tuple(_coerce_loft_section(section) for section in self.sections)
        if len(sections) < 2:
            raise ValidationError("SectionLoftSpec.sections must contain at least two sections")
        object.__setattr__(self, "sections", sections)

        if self.path is not None:
            object.__setattr__(
                self, "path",
                tuple(_as_vec3(point, name="path[]") for point in self.path),
            )
        if self.guide_curves is not None:
            guide_curves = {
                str(name): tuple(_as_vec3(point, name="guide_curves[%r][]" % name) for point in pts)
                for name, pts in self.guide_curves.items()
            }
            object.__setattr__(self, "guide_curves", guide_curves)

        if self.symmetry is not None and self.symmetry != "mirror_yz":
            raise ValidationError("symmetry must be 'mirror_yz' or None")
        if self.degree < 1:
            raise ValidationError("degree must be >= 1")
        if len(self.weights) != 3:
            raise ValidationError("weights must contain exactly 3 values")
        object.__setattr__(self, "degree", int(self.degree))
        object.__setattr__(
            self, "weights",
            (float(self.weights[0]), float(self.weights[1]), float(self.weights[2])),
        )

def _coerce_loft_section(value):
    if isinstance(value, LoftSection):
        return value
    return LoftSection(points=tuple(value))

def _coerce_loft_spec(spec):
    if isinstance(spec, SectionLoftSpec):
        return spec
    return SectionLoftSpec(sections=tuple(_coerce_loft_section(section) for section in spec))

def _build_section_wires(spec):
    cq_shapes = _cq_shapes()
    wires = []
    for idx, section in enumerate(spec.sections):
        points = tuple(section.points)
        try:
            wire = cq_shapes.polygon(*points)
        except Exception as exc:
            raise ValidationError("Failed to build wire for section[%d]" % idx)
        wires.append(wire)
    return wires

def _curve_from_points(points, *, name):
    cq_shapes = _cq_shapes()
    if len(points) < 2:
        raise ValidationError("%s must contain at least 2 points" % name)
    if len(points) == 2:
        return cq_shapes.segment(points[0], points[1])
    try:
        return cq_shapes.spline(*points)
    except Exception:
        try:
            return cq_shapes.polyline(*points)
        except Exception as exc:
            raise ValidationError("Failed to build %s" % name)

def _resolve_path_points(spec):
    if spec.path is not None:
        return spec.path
    if spec.guide_curves is None:
        return None
    return spec.guide_curves.get("spine")

def _resolve_aux_spine_points(spec):
    if spec.guide_curves is None:
        return None
    aux = spec.guide_curves.get("aux_spine")
    if aux is not None:
        return aux
    return spec.guide_curves.get("binormal")

def _validate_guide_curve_names(spec):
    if spec.guide_curves is None:
        return
    supported = {"spine", "aux_spine", "binormal"}
    unsupported = sorted(set(spec.guide_curves) - supported)
    if unsupported:
        raise ValidationError(
            "Unsupported guide_curves keys: "
            + ", ".join(repr(name) for name in unsupported)
            + ". Supported keys are 'spine', 'aux_spine', and 'binormal'."
        )

def _apply_symmetry_shape(shape, *, symmetry):
    if symmetry is None:
        return shape
    if symmetry != "mirror_yz":
        raise ValidationError("Unsupported symmetry mode: %r" % symmetry)
    try:
        mirrored = shape.mirror("YZ")
        if hasattr(shape, "fuse"):
            fused = shape.fuse(mirrored, glue=True)
        else:
            fused = shape
        if hasattr(fused, "fix"):
            fused = fused.fix()
        if hasattr(fused, "clean"):
            fused = fused.clean()
        return fused
    except Exception as exc:
        raise ValidationError("Failed to apply mirror_yz symmetry")

def _heal_shape(shape, *, solid):
    cq_shapes = _cq_shapes()
    if hasattr(shape, "fix"):
        shape = shape.fix()
    if solid:
        try:
            shape = cq_shapes.solid(shape)
        except Exception:
            pass
        if hasattr(shape, "fix"):
            shape = shape.fix()
    return shape

def section_loft(spec, /, **overrides):
    if overrides:
        spec = SectionLoftSpec(**({**_coerce_loft_spec(spec).__dict__, **overrides}))
    else:
        spec = _coerce_loft_spec(spec)

    cq_shapes = _cq_shapes()
    _validate_guide_curve_names(spec)
    wires = _build_section_wires(spec)
    path_points = _resolve_path_points(spec)
    aux_spine_points = _resolve_aux_spine_points(spec)

    if path_points is None:
        shape = cq_shapes.loft(
            wires,
            cap=bool(spec.cap and spec.solid),
            ruled=bool(spec.ruled),
            continuity=spec.continuity,
            parametrization=spec.parametrization,
            degree=int(spec.degree),
            compat=bool(spec.compat),
            smoothing=bool(spec.smoothing),
            weights=spec.weights,
        )
    else:
        path_curve = _curve_from_points(path_points, name="path")
        mode = None
        if aux_spine_points is not None:
            mode = _curve_from_points(aux_spine_points, name="guide_curves['aux_spine']")
        shape = cq_shapes.Solid.sweep_multi(
            wires,
            path_curve,
            makeSolid=bool(spec.solid and spec.cap),
            isFrenet=False,
            mode=mode,
        )

    shape = _apply_symmetry_shape(shape, symmetry=spec.symmetry)

    if spec.repair in {"auto", "kernel"}:
        shape = _heal_shape(shape, solid=bool(spec.solid and spec.cap))

    return MeshGeometry()._set(shape)

# ===== sweeps (33 syms) =====
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
def _mesh(name: str, geometry):
    return mesh_from_geometry(geometry, name)
def _make_envelope_mesh():
    """Long, gently tapered observation-airship gas envelope."""
    stations = [
        (-24.0, 0.22, 0.22, 9.05),
        (-21.5, 1.55, 1.45, 9.05),
        (-17.0, 3.45, 3.25, 9.08),
        (-10.0, 4.55, 4.20, 9.15),
        (-2.0, 5.10, 4.55, 9.18),
        (7.0, 5.25, 4.65, 9.16),
        (15.0, 4.35, 3.85, 9.08),
        (21.0, 2.10, 1.95, 9.02),
        (24.0, 0.24, 0.24, 9.00),
    ]
    loops = []
    for x, radius_y, radius_z, center_z in stations:
        loop = []
        for i in range(72):
            theta = 2.0 * math.pi * i / 72
            loop.append((x, radius_y * math.cos(theta), center_z + radius_z * math.sin(theta)))
        loops.append(loop)
    return section_loft(loops)
def _make_gondola_mesh():
    """Small rounded observation gondola with a blunt glazed bow."""
    stations = [
        (-3.70, 0.12, 0.16, -1.05),
        (-3.15, 0.58, 0.60, -1.08),
        (-2.20, 1.02, 0.98, -1.05),
        (-0.60, 1.15, 1.10, -1.02),
        (1.35, 1.09, 1.05, -1.00),
        (2.85, 0.78, 0.82, -0.98),
        (3.55, 0.20, 0.24, -0.98),
    ]
    loops = []
    for x, radius_y, radius_z, center_z in stations:
        loop = []
        for i in range(48):
            theta = 2.0 * math.pi * i / 48
            # Slightly flatter bottom than top, typical of small gondola shells.
            z_scale = 0.88 if math.sin(theta) < 0.0 else 1.0
            loop.append((x, radius_y * math.cos(theta), center_z + radius_z * z_scale * math.sin(theta)))
        loops.append(loop)
    return section_loft(loops)
def _fin_mesh(name: str, profile: list[tuple[float, float]], thickness: float = 0.14):
    # Profile is authored in the local X/Z plane; rotate the extrusion so its
    # thickness is along local Y.
    geom = ExtrudeGeometry(profile, thickness, center=True).rotate_x(math.pi / 2.0)
    return _mesh(name, geom)
def _add_tube(part, name: str, points, radius: float, material) -> None:
    part.visual(
        _mesh(name, tube_from_spline_points(points, radius=radius, samples_per_segment=2, radial_segments=16)),
        material=material,
        name=name,
    )
def _add_engine(model, gondola, *, side: float, grey, steel, dark, prop_mat) -> None:
    side_name = "left" if side > 0.0 else "right"
    engine = model.part(f"{side_name}_engine")
    # Nacelle local frame: +X forward, +/-Y outboard, Z up.
    engine.visual(
        Cylinder(radius=0.44, length=1.45),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=grey,
        name="nacelle_shell",
    )
    engine.visual(
        Cylinder(radius=0.22, length=0.25),
        origin=Origin(xyz=(0.83, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark,
        name="intake_lip",
    )
    engine.visual(
        Cylinder(radius=0.12, length=0.18),
        origin=Origin(xyz=(-0.74, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="prop_shaft",
    )
    # Two faired struts carry the side-mounted nacelle back to the gondola.
    _add_tube(
        engine,
        f"{side_name}_engine_upper_strut",
        [(-0.25, 0.02, 0.30), (-0.55, -side * 1.58, -0.02)],
        0.045,
        steel,
    )
    _add_tube(
        engine,
        f"{side_name}_engine_lower_strut",
        [(0.30, 0.02, -0.26), (-0.20, -side * 1.52, -0.78)],
        0.040,
        steel,
    )
    engine.visual(
        Box((0.70, 0.10, 0.16)),
        origin=Origin(xyz=(-0.36, -side * 1.35, -0.04)),
        material=steel,
        name="mount_pad",
    )

    model.articulation(
        f"gondola_to_{side_name}_engine",
        ArticulationType.FIXED,
        parent=gondola,
        child=engine,
        origin=Origin(xyz=(-1.55, side * 2.58, -0.75)),
    )

    prop = model.part(f"{side_name}_propeller")
    prop.visual(
        _mesh(
            f"{side_name}_propeller_rotor",
            FanRotorGeometry(
                0.82,
                0.16,
                4,
                thickness=0.095,
                blade_pitch_deg=34.0,
                blade_sweep_deg=18.0,
                blade=FanRotorBlade(shape="scimitar", tip_pitch_deg=16.0, camber=0.18),
                hub=FanRotorHub(style="spinner", rear_collar_height=0.035, rear_collar_radius=0.12),
            ),
        ),
        material=prop_mat,
        name="rotor",
    )
    # The joint frame rotates local +Z into the nacelle's longitudinal +X axis.
    model.articulation(
        f"{side_name}_propeller_spin",
        ArticulationType.CONTINUOUS,
        parent=engine,
        child=prop,
        origin=Origin(xyz=(-0.885, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=90.0),
    )
def _add_wheel(model, gondola, *, side: float, rubber, wheel_mat, dark) -> None:
    side_name = "left" if side > 0.0 else "right"
    wheel = model.part(f"{side_name}_wheel")
    tire = TireGeometry(
        0.42,
        0.24,
        inner_radius=0.30,
        carcass=TireCarcass(belt_width_ratio=0.70, sidewall_bulge=0.05),
        tread=TireTread(style="ribbed", depth=0.018, count=20, land_ratio=0.64),
        grooves=(TireGroove(center_offset=0.0, width=0.018, depth=0.006),),
        sidewall=TireSidewall(style="rounded", bulge=0.05),
        shoulder=TireShoulder(width=0.020, radius=0.010),
    )
    wheel.visual(
        _mesh(f"{side_name}_wheel_tire", tire),
        # Wheel/Tire helpers spin about local X. Rotate that local X to the
        # child-frame Y axle so the continuous joint turns the tire correctly.
        origin=Origin(rpy=(0.0, 0.0, math.pi / 2.0)),
        material=rubber,
        name="tire",
    )
    rim = WheelGeometry(
        0.30,
        0.22,
        rim=WheelRim(inner_radius=0.18, flange_height=0.025, flange_thickness=0.010),
        hub=WheelHub(radius=0.095, width=0.18, cap_style="domed"),
        face=WheelFace(dish_depth=0.018, front_inset=0.006, rear_inset=0.006),
        spokes=WheelSpokes(style="straight", count=6, thickness=0.012, window_radius=0.036),
        bore=WheelBore(style="round", diameter=0.045),
    )
    wheel.visual(
        _mesh(f"{side_name}_wheel_rim", rim),
        origin=Origin(rpy=(0.0, 0.0, math.pi / 2.0)),
        material=wheel_mat,
        name="rim",
    )
    wheel.visual(
        Cylinder(radius=0.085, length=0.08),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark,
        name="hub_cap",
    )

    model.articulation(
        f"{side_name}_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=gondola,
        child=wheel,
        origin=Origin(xyz=(-0.65, side * 1.16, -3.25)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=45.0),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="surveillance_blimp")

    envelope_fabric = model.material("envelope_fabric", rgba=(0.86, 0.88, 0.84, 1.0))
    blue = model.material("blue_marking", rgba=(0.08, 0.25, 0.55, 1.0))
    gondola_white = model.material("gondola_white", rgba=(0.88, 0.90, 0.88, 1.0))
    glass = model.material("blue_glass", rgba=(0.25, 0.55, 0.72, 0.46))
    dark = model.material("dark_composite", rgba=(0.07, 0.08, 0.09, 1.0))
    steel = model.material("brushed_steel", rgba=(0.55, 0.57, 0.58, 1.0))
    nacelle_grey = model.material("nacelle_grey", rgba=(0.48, 0.50, 0.50, 1.0))
    prop_black = model.material("prop_black", rgba=(0.035, 0.035, 0.035, 1.0))
    rubber = model.material("rubber", rgba=(0.02, 0.02, 0.018, 1.0))
    wheel_aluminum = model.material("wheel_aluminum", rgba=(0.72, 0.73, 0.72, 1.0))
    control_fabric = model.material("tail_fabric", rgba=(0.78, 0.80, 0.78, 1.0))

    envelope = model.part("envelope")
    envelope.visual(_mesh("long_surveillance_envelope", _make_envelope_mesh()), material=envelope_fabric, name="hull")
    # A blue service stripe and belly keel make the scale and orientation legible.
    envelope.visual(
        Box((21.0, 0.035, 0.45)),
        origin=Origin(xyz=(2.0, 5.12, 8.55)),
        material=blue,
        name="side_stripe",
    )
    envelope.visual(
        Box((21.0, 0.035, 0.45)),
        origin=Origin(xyz=(2.0, -5.12, 8.55)),
        material=blue,
        name="side_stripe_mirror",
    )
    envelope.visual(
        Cylinder(radius=0.10, length=18.0),
        origin=Origin(xyz=(4.8, 0.0, 4.55), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="keel_rail",
    )
    envelope.visual(
        Cylinder(radius=0.080, length=0.92),
        origin=Origin(xyz=(-24.30, 0.0, 9.05), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="tail_stinger",
    )
    envelope.visual(
        Cylinder(radius=0.065, length=1.15),
        origin=Origin(xyz=(-23.62, 0.0, 9.66)),
        material=steel,
        name="vertical_tail_pylon",
    )
    # Four V-struts hang the gondola from the envelope and keep the cabin visibly
    # supported instead of floating.
    _add_tube(envelope, "front_keel_strut_0", [(7.2, -0.82, 4.72), (7.1, -0.46, 3.72)], 0.060, steel)
    _add_tube(envelope, "front_keel_strut_1", [(7.2, 0.82, 4.72), (7.1, 0.46, 3.72)], 0.060, steel)
    _add_tube(envelope, "rear_keel_strut_0", [(2.2, -0.82, 4.70), (2.1, -0.46, 3.72)], 0.060, steel)
    _add_tube(envelope, "rear_keel_strut_1", [(2.2, 0.82, 4.70), (2.1, 0.46, 3.72)], 0.060, steel)

    gondola = model.part("gondola")
    gondola.visual(_mesh("sensor_gondola_shell", _make_gondola_mesh()), material=gondola_white, name="shell")
    gondola.visual(
        Box((6.25, 1.18, 0.060)),
        origin=Origin(xyz=(-0.35, 0.0, -0.030)),
        material=steel,
        name="roof_hardpoint",
    )
    gondola.visual(
        Box((1.45, 1.02, 0.12)),
        origin=Origin(xyz=(-0.65, 0.0, -2.04)),
        material=steel,
        name="gear_mount_plate",
    )
    gondola.visual(
        Box((1.35, 2.24, 0.42)),
        origin=Origin(xyz=(2.55, 0.0, -0.74)),
        material=glass,
        name="bow_observation_glass",
    )
    for x in (-1.25, -0.20, 0.85):
        gondola.visual(
            Box((0.55, 0.035, 0.52)),
            origin=Origin(xyz=(x, 1.12, -0.73)),
            material=glass,
            name=f"window_{x:.1f}_a",
        )
        gondola.visual(
            Box((0.55, 0.035, 0.52)),
            origin=Origin(xyz=(x, -1.12, -0.73)),
            material=glass,
            name=f"window_{x:.1f}_b",
        )
    # Fixed EO/IR sensor ball under the observation cabin.
    gondola.visual(Cylinder(radius=0.13, length=0.45), origin=Origin(xyz=(1.15, 0.0, -2.05)), material=dark, name="sensor_neck")
    gondola.visual(Cylinder(radius=0.34, length=0.40), origin=Origin(xyz=(1.15, 0.0, -2.38)), material=dark, name="sensor_turret")
    gondola.visual(Box((0.22, 0.08, 0.14)), origin=Origin(xyz=(1.48, 0.0, -2.38)), material=glass, name="sensor_window")
    # Real undercarriage: cross beam, splayed struts, and fork plates at each wheel.
    gondola.visual(
        Cylinder(radius=0.055, length=2.40),
        origin=Origin(xyz=(-0.65, 0.0, -2.68), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="gear_cross_axle",
    )
    for side in (-1.0, 1.0):
        _add_tube(gondola, f"gear_front_strut_{side:+.0f}", [(-0.10, side * 0.40, -2.05), (-0.65, side * 0.98, -3.02)], 0.045, steel)
        _add_tube(gondola, f"gear_rear_strut_{side:+.0f}", [(-1.24, side * 0.40, -2.05), (-0.65, side * 0.98, -3.02)], 0.045, steel)
        gondola.visual(
            Box((0.10, 0.035, 0.58)),
            origin=Origin(xyz=(-0.65, side * 1.00, -3.08)),
            material=steel,
            name=f"wheel_fork_inner_{side:+.0f}",
        )
        gondola.visual(
            Box((0.10, 0.035, 0.58)),
            origin=Origin(xyz=(-0.65, side * 1.36, -3.08)),
            material=steel,
            name=f"wheel_fork_outer_{side:+.0f}",
        )
        gondola.visual(
            Box((0.12, 0.46, 0.090)),
            origin=Origin(xyz=(-0.65, side * 1.155, -2.745)),
            material=steel,
            name=f"wheel_fork_bridge_{side:+.0f}",
        )
        gondola.visual(
            Cylinder(radius=0.052, length=0.44),
            origin=Origin(xyz=(-0.65, side * 1.16, -3.25), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=steel,
            name=f"axle_stub_{side:+.0f}",
        )

    model.articulation(
        "envelope_to_gondola",
        ArticulationType.FIXED,
        parent=envelope,
        child=gondola,
        origin=Origin(xyz=(5.0, 0.0, 3.72)),
    )

    _add_engine(model, gondola, side=1.0, grey=nacelle_grey, steel=steel, dark=dark, prop_mat=prop_black)
    _add_engine(model, gondola, side=-1.0, grey=nacelle_grey, steel=steel, dark=dark, prop_mat=prop_black)
    _add_wheel(model, gondola, side=1.0, rubber=rubber, wheel_mat=wheel_aluminum, dark=dark)
    _add_wheel(model, gondola, side=-1.0, rubber=rubber, wheel_mat=wheel_aluminum, dark=dark)

    vertical_tail = model.part("vertical_tail")
    vertical_tail.visual(
        _fin_mesh("vertical_fixed_fin", [(0.02, 0.00), (1.45, 0.34), (1.60, 2.04), (0.02, 2.58)]),
        material=control_fabric,
        name="fin_panel",
    )
    vertical_tail.visual(
        Cylinder(radius=0.055, length=3.45),
        origin=Origin(xyz=(0.035, 0.0, 1.22)),
        material=steel,
        name="rudder_hinge_post",
    )
    model.articulation(
        "envelope_to_vertical_tail",
        ArticulationType.FIXED,
        parent=envelope,
        child=vertical_tail,
        origin=Origin(xyz=(-23.78, 0.0, 10.20)),
    )

    rudder = model.part("rudder")
    rudder.visual(
        _fin_mesh("rudder_control_surface", [(-1.18, 0.10), (-0.04, 0.08), (-0.04, 2.36), (-1.05, 1.95)]),
        material=control_fabric,
        name="rudder_panel",
    )
    rudder.visual(
        Cylinder(radius=0.045, length=3.05),
        origin=Origin(xyz=(-0.035, 0.0, 1.18)),
        material=steel,
        name="rudder_hinge_knuckle",
    )
    model.articulation(
        "rudder_hinge",
        ArticulationType.REVOLUTE,
        parent=vertical_tail,
        child=rudder,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=12.0, velocity=1.4, lower=-0.55, upper=0.55),
    )

    horizontal_tail = model.part("horizontal_tail")
    horizontal_tail.visual(
        Cylinder(radius=0.070, length=8.7),
        origin=Origin(xyz=(0.0, 0.0, 0.10), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="elevator_hinge_spar",
    )
    for side in (-1.0, 1.0):
        horizontal_tail.visual(
            Box((1.20, 0.18, 0.12)),
            origin=Origin(xyz=(0.55, side * 2.14, 0.20)),
            material=steel,
            name=f"stabilizer_root_rib_{side:+.0f}",
        )
        horizontal_tail.visual(
            Box((1.65, 2.15, 0.13)),
            origin=Origin(xyz=(1.18, side * 3.20, 0.10)),
            material=control_fabric,
            name=f"stabilizer_panel_{side:+.0f}",
        )
    model.articulation(
        "envelope_to_horizontal_tail",
        ArticulationType.FIXED,
        parent=envelope,
        child=horizontal_tail,
        origin=Origin(xyz=(-24.55, 0.0, 9.05)),
    )

    elevator = model.part("elevator")
    elevator.visual(
        Cylinder(radius=0.045, length=8.5),
        origin=Origin(xyz=(0.0, 0.0, 0.02), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="elevator_torque_tube",
    )
    for side in (-1.0, 1.0):
        elevator.visual(
            Box((1.25, 2.10, 0.11)),
            origin=Origin(xyz=(-0.66, side * 3.20, 0.02)),
            material=control_fabric,
            name=f"elevator_panel_{side:+.0f}",
        )
    model.articulation(
        "elevator_hinge",
        ArticulationType.REVOLUTE,
        parent=horizontal_tail,
        child=elevator,
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=1.2, lower=-0.42, upper=0.42),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
